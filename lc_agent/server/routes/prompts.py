# lc_agent/server/routes/prompts.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from lc_agent.core.engine import AgentEngine
from lc_agent.db.engine import get_async_session as _get_db_session
from lc_agent.db.models import AgentPresetDB
from lc_agent.db.models_auth import User
from lc_agent.db.repository import PromptRepository
from lc_agent.server.auth_middleware import get_current_user, require_admin
from lc_agent.server.dependencies import get_engine
from sqlalchemy import select

router = APIRouter(tags=["prompts"])


async def get_db(request: Request):
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    session = _get_db_session(db_url)
    try:
        yield session
    finally:
        await session.close()


class PromptCreateRequest(BaseModel):
    name: str
    content: str = ""


class PromptUpdateRequest(BaseModel):
    name: str | None = None
    content: str | None = None


class BindingUpdateRequest(BaseModel):
    prompt_ids: list[str]


def _prompt_to_dict(pt) -> dict:
    return {
        "id": pt.id,
        "name": pt.name,
        "content": pt.content,
        "created_at": pt.created_at.isoformat(),
        "updated_at": pt.updated_at.isoformat(),
    }


# ─── Prompt Template CRUD ───────────────────────────────────────────────

@router.get("/prompts")
async def list_prompts(
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = PromptRepository(db)
    pts = await repo.list_all()
    return [_prompt_to_dict(pt) for pt in pts]


@router.post("/prompts", status_code=201)
async def create_prompt(
    body: PromptCreateRequest,
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = PromptRepository(db)
    pt = await repo.create(name=body.name, content=body.content)
    return _prompt_to_dict(pt)


@router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    body: PromptUpdateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = PromptRepository(db)
    kwargs = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    pt = await repo.update(prompt_id, **kwargs)
    if pt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Refresh engine presets for all agents using this prompt
    affected_ids = await repo.get_agent_ids_using_prompt(prompt_id)
    for agent_id in affected_ids:
        await _refresh_engine_preset_prompts(agent_id, engine, repo)

    return _prompt_to_dict(pt)


@router.delete("/prompts/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = PromptRepository(db)
    affected_ids = await repo.get_agent_ids_using_prompt(prompt_id)
    if affected_ids:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Prompt is in use by agents",
                "agent_ids": affected_ids,
            },
        )
    deleted = await repo.delete(prompt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return Response(status_code=204)


# ─── Agent ↔ Prompt bindings ─────────────────────────────────────────────

@router.get("/agents/{agent_id}/prompts")
async def get_agent_prompts(
    agent_id: str,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return ordered list of prompt IDs bound to this agent."""
    repo = PromptRepository(db)
    bindings = await repo.get_bindings_for_agent(agent_id)
    return [b.prompt_id for b in bindings]


@router.put("/agents/{agent_id}/prompts")
async def set_agent_prompts(
    agent_id: str,
    body: BindingUpdateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Replace all prompt bindings for an agent."""
    # Validate agent exists
    if not engine._preset_exists(agent_id):
        stmt = select(AgentPresetDB).where(AgentPresetDB.id == agent_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Agent not found")

    # Validate all prompt IDs exist
    repo = PromptRepository(db)
    for pid in body.prompt_ids:
        if await repo.get_by_id(pid) is None:
            raise HTTPException(status_code=422, detail=f"Prompt not found: {pid}")

    await repo.set_bindings_for_agent(agent_id, body.prompt_ids)
    await _refresh_engine_preset_prompts(agent_id, engine, repo)

    return [b.prompt_id for b in await repo.get_bindings_for_agent(agent_id)]


# ─── Helpers ─────────────────────────────────────────────────────────────

async def _refresh_engine_preset_prompts(
    agent_id: str,
    engine: AgentEngine,
    repo: PromptRepository,
) -> None:
    """Update engine's in-memory preset with fresh extra_system_prompts and invalidate cache."""
    extra = await repo.resolve_extra_prompts(agent_id)
    preset = engine._presets.get(agent_id)
    if preset is not None:
        engine._presets[agent_id] = preset.model_copy(update={"extra_system_prompts": extra})
    engine.invalidate_agent_cache(agent_id)
