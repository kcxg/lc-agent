from fastapi import APIRouter, Depends

from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["models"])


@router.get("/models")
def list_models(
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """List all configured models."""
    return [
        {
            "id": m.id,
            "provider": m.provider,
            "base_url": m.base_url,
            "context_limit": m.context_limit,
        }
        for m in engine.get_models()
    ]
