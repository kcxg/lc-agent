import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select

from lc_agent.core.engine import AgentEngine
from lc_agent.core.models import AgentPreset, SubAgentLink
from lc_agent.db.engine import get_async_session as _get_db_session
from lc_agent.db.models import AgentPresetDB
from lc_agent.db.models_auth import User, UserAgentAccess
from lc_agent.server.auth_middleware import get_current_user, require_admin
from lc_agent.server.dependencies import get_engine

router = APIRouter(tags=["agents"])


async def get_db(request: Request):
    db_url = request.app.state.config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
    session = _get_db_session(db_url)
    try:
        yield session
    finally:
        await session.close()


class AgentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    system_prompt: str
    default_model: str
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool = False

    @field_validator("subagents")
    @classmethod
    def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None:
        if value is None:
            return value
        seen_ids: set[str] = set()
        for item in value:
            if not item.delegation_description.strip():
                raise ValueError("delegation_description must not be blank")
            if item.agent_id in seen_ids:
                raise ValueError(f"duplicate subagent agent_id: {item.agent_id}")
            seen_ids.add(item.agent_id)
        return value


class AgentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    system_prompt: str | None = None
    default_model: str | None = None
    allowed_tool_groups: list[str] | None = None
    allowed_mcp_servers: list[str] | None = None
    allowed_skills: list[str] | None = None
    llm_params: dict | None = None
    subagents: list[SubAgentLink] | None = None
    enable_general_purpose_subagent: bool | None = None

    @field_validator("subagents")
    @classmethod
    def validate_subagents(cls, value: list[SubAgentLink] | None) -> list[SubAgentLink] | None:
        if value is None:
            return value
        seen_ids: set[str] = set()
        for item in value:
            if not item.delegation_description.strip():
                raise ValueError("delegation_description must not be blank")
            if item.agent_id in seen_ids:
                raise ValueError(f"duplicate subagent agent_id: {item.agent_id}")
            seen_ids.add(item.agent_id)
        return value


def _preset_to_dict(p: AgentPreset) -> dict:
    data = p.model_dump()
    if data.get("subagents") is not None:
        data["subagents"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in data["subagents"]]
    if p.source == "code":
        return {
            "id": p.id,
            "name": p.name,
            "system_prompt": p.system_prompt,
            "default_model": "custom",
            "allowed_tool_groups": [],
            "allowed_mcp_servers": [],
            "allowed_skills": [],
            "source": "code",
            "default_enabled": False,
            "subagents": data.get("subagents"),
            "enable_general_purpose_subagent": False,
        }
    data["source"] = p.source
    data["default_enabled"] = p.default_enabled
    return data


@router.get("/agents")
async def list_agents(
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all agent presets (builtin + code + DB-persisted)."""
    result = []

    for bp in engine.get_builtin_presets():
        result.append(_preset_to_dict(bp))

    for p in engine._custom_presets.values():
        result.append(_preset_to_dict(p))

    stmt = select(AgentPresetDB)
    rows = await db.execute(stmt)
    for row in rows.scalars().all():
        result.append({
            "id": row.id,
            "name": row.name,
            "system_prompt": row.system_prompt,
            "default_model": row.default_model,
            "allowed_tool_groups": row.allowed_tool_groups,
            "allowed_mcp_servers": row.allowed_mcp_servers,
            "allowed_skills": row.allowed_skills,
            "llm_params": row.llm_params,
            "source": "user",
            "default_enabled": True,
            "subagents": row.subagents,
            "enable_general_purpose_subagent": row.enable_general_purpose_subagent,
        })

    if user.role != "admin":
        access_stmt = select(UserAgentAccess.agent_id).where(UserAgentAccess.user_id == user.id)
        access_rows = await db.execute(access_stmt)
        allowed_ids = set(access_rows.scalars().all())
        result = [a for a in result if a["id"] in allowed_ids]

    return result


def _validate_subagent_ids_exist(engine: AgentEngine, subagents: list[SubAgentLink] | None) -> None:
    """Validate that every subagent agent_id refers to a known preset."""
    if not subagents:
        return
    for link in subagents:
        if not engine._preset_exists(link.agent_id):
            raise HTTPException(
                status_code=422,
                detail=f"subagent agent_id not found: {link.agent_id}",
            )


@router.post("/agents", status_code=201)
async def create_agent(
    body: AgentCreateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Create a new agent preset (persisted to DB)."""
    _validate_subagent_ids_exist(engine, body.subagents)
    preset_db = AgentPresetDB(
        id=str(uuid.uuid4()),
        name=body.name,
        system_prompt=body.system_prompt,
        default_model=body.default_model,
        allowed_tool_groups=body.allowed_tool_groups,
        allowed_mcp_servers=body.allowed_mcp_servers,
        allowed_skills=body.allowed_skills,
        llm_params=body.llm_params,
        subagents=[item.model_dump() for item in body.subagents] if body.subagents else None,
        enable_general_purpose_subagent=body.enable_general_purpose_subagent,
    )
    db.add(preset_db)
    await db.commit()
    await db.refresh(preset_db)

    preset = AgentPreset(
        id=preset_db.id,
        name=preset_db.name,
        system_prompt=preset_db.system_prompt,
        default_model=preset_db.default_model,
        allowed_tool_groups=preset_db.allowed_tool_groups,
        allowed_mcp_servers=preset_db.allowed_mcp_servers,
        allowed_skills=preset_db.allowed_skills,
        llm_params=preset_db.llm_params,
        subagents=[SubAgentLink.model_validate(item) for item in preset_db.subagents] if preset_db.subagents else None,
        enable_general_purpose_subagent=preset_db.enable_general_purpose_subagent,
    )
    engine._presets[preset.id] = preset

    return _preset_to_dict(preset)


@router.get("/agents/available-subagents")
async def list_available_subagents(
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Return all presets that can be used as sub-agents.

    Excludes __chat__ builtin. Includes code agents and web presets.
    """
    result = []

    for p in engine._custom_presets.values():
        result.append({
            "id": p.id,
            "name": p.name,
            "source": "code",
            "description": p.default_delegation_description or "",
        })

    for bp in engine.get_builtin_presets():
        if bp.id == "__chat__":
            continue
        result.append({
            "id": bp.id,
            "name": bp.name,
            "source": "builtin",
            "description": bp.default_delegation_description or "",
        })

    stmt = select(AgentPresetDB)
    rows = await db.execute(stmt)
    for row in rows.scalars().all():
        result.append({
            "id": row.id,
            "name": row.name,
            "source": "user",
            "description": "",
        })

    return result


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdateRequest,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update an agent preset."""
    if agent_id in engine.BUILTIN_IDS:
        raise HTTPException(status_code=400, detail="Cannot edit builtin agent")

    _validate_subagent_ids_exist(engine, body.subagents)
    update_data = body.model_dump(exclude_unset=True)

    if agent_id in engine._custom_presets:
        raise HTTPException(
            status_code=403,
            detail="Code agents are defined by their registered graph and cannot be edited from the UI",
        )

    stmt = select(AgentPresetDB).where(AgentPresetDB.id == agent_id)
    result = await db.execute(stmt)
    preset_db = result.scalar_one_or_none()
    if preset_db is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    for key, value in update_data.items():
        setattr(preset_db, key, value)
    preset_db.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(preset_db)

    preset = AgentPreset(
        id=preset_db.id,
        name=preset_db.name,
        system_prompt=preset_db.system_prompt,
        default_model=preset_db.default_model,
        allowed_tool_groups=preset_db.allowed_tool_groups,
        allowed_mcp_servers=preset_db.allowed_mcp_servers,
        allowed_skills=preset_db.allowed_skills,
        llm_params=preset_db.llm_params,
        subagents=[SubAgentLink.model_validate(item) for item in preset_db.subagents] if preset_db.subagents else None,
        enable_general_purpose_subagent=preset_db.enable_general_purpose_subagent,
    )
    engine._presets[preset.id] = preset
    engine.invalidate_agent_cache(agent_id)

    return _preset_to_dict(preset)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    engine: AgentEngine = Depends(get_engine),
    db=Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete an agent preset."""
    if agent_id in engine.BUILTIN_IDS:
        raise HTTPException(status_code=400, detail="Cannot delete builtin agent")
    if agent_id in engine._custom_presets:
        raise HTTPException(status_code=403, detail="Cannot delete code-registered agent")

    stmt = select(AgentPresetDB).where(AgentPresetDB.id == agent_id)
    result = await db.execute(stmt)
    preset_db = result.scalar_one_or_none()
    if preset_db is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(preset_db)
    await db.commit()

    engine._presets.pop(agent_id, None)
    engine.invalidate_agent_cache(agent_id)

    return Response(status_code=204)


@router.post("/agents/{agent_id}/activate")
def activate_agent(
    agent_id: str,
    request: Request,
    engine: AgentEngine = Depends(get_engine),
    admin: User = Depends(require_admin),
):
    """Apply an agent's default toggle state to MCP servers and tool groups.

    - Agents with default_enabled=False (Empty): disable all MCP + tool groups
    - Agents with default_enabled=True (Power): enable all MCP + tool groups
    - Chat agent (allowed=[]): no change needed (preset blocks everything)
    """
    from lc_agent.tools.registry import ToolRegistry

    preset = engine._resolve_preset(agent_id)
    if preset.source == "code" or agent_id in engine._custom_presets:
        return {
            "agent_id": agent_id,
            "action": "none",
            "reason": "code agent is controlled by its registered graph",
        }
    manager = getattr(request.app.state, "mcp_manager", None)
    registry = ToolRegistry()

    if preset.allowed_tool_groups == [] and preset.allowed_mcp_servers == []:
        return {"agent_id": agent_id, "action": "none", "reason": "preset blocks all"}

    target_enabled = preset.default_enabled

    changed_mcp = []
    if manager:
        for server in manager.servers:
            if server.enabled != target_enabled:
                server.enabled = target_enabled
                if not target_enabled:
                    server.status = "disabled"
                elif server.name in manager._sessions:
                    server.status = "connected"
                else:
                    server.status = "disconnected"
                changed_mcp.append(server.name)

    changed_groups = []
    for group in registry.get_group_names():
        is_disabled = group in registry._disabled_groups
        if target_enabled and is_disabled:
            registry._disabled_groups.discard(group)
            changed_groups.append(group)
        elif not target_enabled and not is_disabled:
            registry._disabled_groups.add(group)
            changed_groups.append(group)

    if changed_mcp or changed_groups:
        engine._mcp_generation += 1

    return {
        "agent_id": agent_id,
        "default_enabled": target_enabled,
        "changed_mcp": changed_mcp,
        "changed_groups": changed_groups,
    }
