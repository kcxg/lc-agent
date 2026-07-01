from fastapi import APIRouter, Depends
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["settings"])


class SummarizationConfig(BaseModel):
    enabled: bool = True
    default_model: str = ""
    trigger: list | None = None
    keep: list | None = None


@router.get("/settings/summarization")
def get_summarization(engine: AgentEngine = Depends(get_engine)):
    """Get current summarization configuration."""
    conf = engine.config.get("agent", {}).get("summarization", {})
    return {
        "enabled": conf.get("enabled", True),
        "default_model": conf.get("default_model", ""),
        "trigger": conf.get("trigger"),
        "keep": conf.get("keep"),
    }


@router.put("/settings/summarization")
def update_summarization(body: SummarizationConfig, engine: AgentEngine = Depends(get_engine)):
    """Update summarization config at runtime (no restart needed)."""
    agent_conf = engine.config.setdefault("agent", {})
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
