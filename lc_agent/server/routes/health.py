# lc_agent/server/routes/health.py
from fastapi import APIRouter, Request

from lc_agent import __version__
from lc_agent.config import get_app_name, get_config

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    config = get_config()
    auth_enabled = (
        hasattr(request.app.state, "auth_service")
        and request.app.state.auth_service is not None
    )
    return {
        "status": "ok",
        "version": __version__,
        "auth_enabled": auth_enabled,
        "config_loaded": config.get("_config_path") is not None,
        "app_name": get_app_name(),
    }
