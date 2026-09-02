from fastapi import APIRouter, Depends
from pydantic import BaseModel

from lc_agent.config import get_config, get_config_value
from lc_agent.core.engine import AgentEngine
from lc_agent.db.models_auth import User
from lc_agent.server.auth_middleware import get_current_user
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["settings"])


class SummarizationConfig(BaseModel):
    enabled: bool = True
    default_model: str = ""
    trigger: list | None = None
    keep: list | None = None


@router.get("/settings/summarization")
def get_summarization(
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """Get current summarization configuration."""
    conf = get_config_value(get_config(), "agent.summarization", {})
    return {
        "enabled": conf.get("enabled", True),
        "default_model": conf.get("default_model", ""),
        "trigger": conf.get("trigger"),
        "keep": conf.get("keep"),
    }


@router.put("/settings/summarization")
def update_summarization(
    body: SummarizationConfig,
    user: User = Depends(get_current_user),
    engine: AgentEngine = Depends(get_engine),
):
    """Update summarization config at runtime (no restart needed)."""
    agent_conf = get_config().setdefault("agent", {})
    summ_conf = agent_conf.setdefault("summarization", {})

    summ_conf["enabled"] = body.enabled
    summ_conf["default_model"] = body.default_model
    if body.trigger is not None:
        summ_conf["trigger"] = body.trigger
    if body.keep is not None:
        summ_conf["keep"] = body.keep

    engine.invalidate_all_agents()

    return {
        "enabled": summ_conf.get("enabled", True),
        "default_model": summ_conf.get("default_model", ""),
        "trigger": summ_conf.get("trigger"),
        "keep": summ_conf.get("keep"),
    }
