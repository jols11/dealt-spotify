from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.demo_seed import generate_demo_events
from app.services.pipeline import rebuild_derived


def test_health():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_unauthenticated_analytics():
    client = TestClient(app)
    response = client.get("/api/analytics/overview")
    assert response.status_code == 401


def test_demo_mode_overview_and_graph(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    db = testing_session()
    user = generate_demo_events(db, days=60, seed=1)
    rebuild_derived(db, user)
    db.close()

    client = TestClient(app)
    enter = client.post("/api/auth/demo")
    assert enter.status_code == 200
    overview = client.get("/api/analytics/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["plays"] > 50
    assert body["user"]["is_demo"] is True
    network = client.get("/api/analytics/transitions")
    assert network.status_code == 200
    assert "nodes" in network.json()
    diversity = client.get("/api/analytics/diversity")
    assert diversity.status_code == 200
    recs = client.get("/api/analytics/recommendations")
    assert recs.status_code == 200
    app.dependency_overrides.clear()
