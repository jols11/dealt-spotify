from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.data import router as data_router
from app.api.discover import router as discover_router
from app.api.hands import router as hands_router
from app.core.config import get_settings
from app.db.session import init_db

settings = get_settings()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        init_db()
        yield

    application = FastAPI(
        title="The Hand",
        version="2.0.0",
        description="Deal a playlist as a stack of poker cards between two Spotify track links.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        same_site="lax",
        https_only=False,
        max_age=60 * 60 * 24 * 14,
    )
    application.include_router(auth_router)
    application.include_router(data_router)
    application.include_router(analytics_router)
    application.include_router(discover_router)
    application.include_router(hands_router)

    @application.get("/api/health")
    def health():
        return {"ok": True}

    return application


app = create_app()
