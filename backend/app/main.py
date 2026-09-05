from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.data import router as data_router
from app.api.discover import router as discover_router
from app.api.hands import router as hands_router
from app.core.config import ROOT_DIR, get_settings
from app.db.session import init_db

settings = get_settings()
DIST_DIR = ROOT_DIR / "frontend" / "dist"


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        init_db()
        yield

    application = FastAPI(
        title="Dealt",
        version="2.2.0",
        description="Search two songs and deal the stack between them.",
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
        https_only=settings.cookie_https_only,
        max_age=60 * 60 * 24 * 14,
    )
    application.include_router(auth_router)
    application.include_router(data_router)
    application.include_router(analytics_router)
    application.include_router(discover_router)
    application.include_router(hands_router)

    @application.get("/api/health")
    def health():
        return {
            "ok": True,
            "spotify_configured": settings.spotify_configured,
            "catalog_ready": settings.catalog_ready,
        }

    @application.get("/")
    def root():
        return spa("")

    @application.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/") or path == "api":
            raise HTTPException(status_code=404, detail="Not found")
        if not DIST_DIR.is_dir():
            raise HTTPException(
                status_code=404,
                detail="UI is not built. During development use the Vite server on port 4177.",
            )
        candidate = (DIST_DIR / path).resolve()
        try:
            candidate.relative_to(DIST_DIR.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Not found") from exc
        if candidate.is_file():
            return FileResponse(candidate)
        index = DIST_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Not found")

    return application


app = create_app()
