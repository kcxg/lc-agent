# lc_agent/server/app.py
import mimetypes
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from lc_agent import __version__
from lc_agent.server.auth import get_auth_config, require_auth
from lc_agent.server.routes.agents import router as agents_router
from lc_agent.server.routes.auth import router as auth_router
from lc_agent.server.routes.health import router as health_router
from lc_agent.server.routes.mcp import router as mcp_router
from lc_agent.server.routes.models import router as models_router
from lc_agent.server.routes.sessions import router as sessions_router
from lc_agent.server.routes.skills import router as skills_router
from lc_agent.server.routes.tools import router as tools_router

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


def create_app(config: dict, lifespan=None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="lc_agent",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.config = config

    auth_settings = get_auth_config(config)
    protected_dependencies = [Depends(require_auth)] if auth_settings.enabled else []

    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(tools_router, prefix="/api", dependencies=protected_dependencies)
    app.include_router(models_router, prefix="/api", dependencies=protected_dependencies)
    app.include_router(agents_router, prefix="/api", dependencies=protected_dependencies)
    app.include_router(sessions_router, prefix="/api", dependencies=protected_dependencies)
    app.include_router(skills_router, prefix="/api", dependencies=protected_dependencies)
    app.include_router(mcp_router, prefix="/api", dependencies=protected_dependencies)

    return app


def mount_static_files(app: FastAPI):
    """Mount static files with SPA fallback that does NOT intercept API routes."""
    web_dist = Path(__file__).parent.parent / "web" / "dist"
    if not web_dist.exists():
        return

    # Serve /assets/* directly (no html=True)
    assets_dir = web_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_html = web_dist / "index.html"

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        favicon_path = web_dist / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(str(favicon_path))
        return HTMLResponse(status_code=404)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Never serve index.html for API paths — let them 404 normally
        if full_path == "api" or full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if index_html.exists():
            return FileResponse(str(index_html))
        return HTMLResponse(status_code=404)
