"""SkillMiddleware integration for the agent engine."""
from typing import Any

from langchain_agentskills import SkillMiddleware

_LOAD_SKILL_DESCRIPTION = (
    "Retrieve the full step-by-step instructions for a skill. "
    "This MUST be called before executing any task that matches a skill — "
    "the brief description in the system prompt is only a trigger hint, "
    "not the actual procedure. "
    "Returns the skill's markdown body, available resources, and scripts. "
    "Skill names are listed in the system prompt under '## Available Skills'."
)


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
        self.tools = [
            t.model_copy(update={"description": _LOAD_SKILL_DESCRIPTION})
            if t.name == "load_skill"
            else t
            for t in self.tools
        ]

    @property
    def has_visible_skills(self) -> bool:
        """True when at least one skill is visible to this preset."""
        return bool(self._skills_prompt and self._skills_prompt.strip())
