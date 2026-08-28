"""SkillMiddleware integration for the agent engine."""
from typing import Any

from langchain_agentskills import SkillMiddleware
from pydantic import BaseModel, ConfigDict, Field

_LOAD_SKILL_DESCRIPTION = (
    "Load a skill by name to get its full instructions. "
    "Returns the skill's markdown body, available resources, and scripts. "
    "Skill names are listed in the system prompt under '## Available Skills'."
)

_READ_SKILL_RESOURCE_DESCRIPTION = (
    "Read a resource file from a skill. "
    "Use load_skill first to see available resources.\n"
    "Parameters:\n"
    "- skill_name: the skill name (from '## Available Skills' in the system prompt)\n"
    "- resource_name: the resource filename to read — must be one of the "
    "resources listed by load_skill, do not guess."
)

_RUN_SKILL_SCRIPT_DESCRIPTION = (
    "Run a script from a skill. "
    "Use load_skill first to see available scripts.\n"
    "Parameters:\n"
    "- skill_name: the skill name (from '## Available Skills' in the system prompt)\n"
    "- script_name: the script filename to run — must be one of the scripts "
    "listed by load_skill, do not guess.\n"
    "- script_args: optional list of string arguments passed to the script."
)

_SKILL_TOOL_DESCRIPTIONS: dict[str, str] = {
    "load_skill": _LOAD_SKILL_DESCRIPTION,
    "read_skill_resource": _READ_SKILL_RESOURCE_DESCRIPTION,
    "run_skill_script": _RUN_SKILL_SCRIPT_DESCRIPTION,
}


# ---------------------------------------------------------------------------
# args_schema 补齐：langchain_agentskills 的三个工具是 BaseTool 子类，
# 但都没有定义 args_schema。没有 args_schema 时 BaseTool._parse_input 会
# 原样透传 tool_input 不做校验，LLM 传错参数名就会漏进 _run(**kwargs) 抛
# TypeError，而 ToolNode 只把 pydantic ValidationError 反馈给模型重试，
# TypeError 会直接中断 agent 运行。这里补上 extra="forbid" 的 pydantic
# schema，让参数名/类型错误走官方自动反馈链路。
# ---------------------------------------------------------------------------

class _LoadSkillArgs(BaseModel):
    """Tool arguments for ``load_skill``."""

    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(description="The name of the skill to load.")


class _ReadSkillResourceArgs(BaseModel):
    """Tool arguments for ``read_skill_resource``."""

    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(description="The name of the skill.")
    resource_name: str = Field(description="The resource filename to read.")


class _RunSkillScriptArgs(BaseModel):
    """Tool arguments for ``run_skill_script``."""

    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(description="The name of the skill.")
    script_name: str = Field(description="The script filename to run.")
    script_args: list[str] | None = Field(
        default=None, description="Optional arguments passed to the script."
    )


_SKILL_TOOL_ARGS_SCHEMAS: dict[str, type[BaseModel]] = {
    "load_skill": _LoadSkillArgs,
    "read_skill_resource": _ReadSkillResourceArgs,
    "run_skill_script": _RunSkillScriptArgs,
}


def _build_skills_prompt(skills: list) -> str:
    """Build the JSON-format skills system-prompt block. Returns empty string when skills list is empty."""
    if not skills:
        return ""
    import json as _json
    skill_entries = [
        {"skill_name": s.name, "description": s.description.splitlines()[0]}
        for s in skills
    ]
    lines = [
        "<available_skills>",
        "## Available Skills",
        "",
        "The descriptions below are **triggers** — they tell you WHEN a skill applies.",
        "The actual step-by-step instructions, required tools, and constraints are INSIDE the skill.",
        "",
        "**MANDATORY RULE**: When the user's request matches a skill's description,",
        "you MUST call `load_skill(skill_name=\"<skill_name>\")` FIRST to retrieve",
        "the full instructions, then follow them exactly.",
        "Do NOT skip this step and proceed with your default approach.",
        "",
        "**DIRECT SKILL COMMAND**: If the user's message contains a standalone `/`",
        "followed immediately by a listed skill name (for example `/coding-assistant`),",
        "treat it as an explicit request to use that skill. You MUST call `load_skill`",
        "for that exact skill name FIRST, then treat the remaining text as the user's task.",
        "",
        "```json",
        _json.dumps(skill_entries, ensure_ascii=False, indent=2),
        "```",
        "",
        "After loading a skill, you may also call `read_skill_resource` to fetch",
        "its reference files or `run_skill_script` to execute its scripts.",
        "</available_skills>",
    ]
    return "\n".join(lines)


class _LcAgentSkillMiddleware(SkillMiddleware):
    """SkillMiddleware with per-preset allowed_skills filtering.

    Wraps the shared loader with ``_AllowedSkillsWrapper`` so only the
    permitted skills for this preset appear in the system prompt and can
    be loaded by the agent.  Also applies the lc-agent JSON prompt format
    and the stricter ``load_skill`` tool description.
    """

    def __init__(
        self,
        loader: Any,
        *,
        allowed_skills: list[str] | None = None,
        executor: Any = None,
    ) -> None:
        from lc_agent.skills.filtered_loader import _AllowedSkillsWrapper
        effective_loader = (
            _AllowedSkillsWrapper(loader, set(allowed_skills))
            if allowed_skills is not None
            else loader
        )
        super().__init__(
            loader=effective_loader,
            executor=executor,
            prompt_builder=_build_skills_prompt,
        )
        # 先取出父类设置的工具实例（self.tools 之后会被重建），
        # 再补上父类缺失的 args_schema（见上方 _SKILL_TOOL_ARGS_SCHEMAS 说明），
        # 并覆盖三个工具的 description（见上方 _SKILL_TOOL_DESCRIPTIONS 说明）。
        original_tools = list(self.tools)
        self.tools = []
        for t in original_tools:
            update: dict[str, Any] = {}
            desc = _SKILL_TOOL_DESCRIPTIONS.get(t.name)
            if desc is not None:
                update["description"] = desc
            schema = _SKILL_TOOL_ARGS_SCHEMAS.get(t.name)
            if schema is not None:
                update["args_schema"] = schema
            self.tools.append(t.model_copy(update=update) if update else t)

    @property
    def has_visible_skills(self) -> bool:
        """True when at least one skill is visible to this preset."""
        return bool(self._skills_prompt and self._skills_prompt.strip())
