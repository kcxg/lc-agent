from lc_agent.core.models import AgentPreset, SubAgentLink


def test_agent_preset_subagents_defaults_to_none():
    p = AgentPreset(id="x", name="n", system_prompt="s", default_model="m")
    assert p.subagents is None


def test_agent_preset_subagents_accepts_list():
    p = AgentPreset(
        id="x",
        name="n",
        system_prompt="s",
        default_model="m",
        subagents=[SubAgentLink(agent_id="a", delegation_description="描述A")],
    )
    assert p.subagents is not None
    assert p.subagents[0].agent_id == "a"
    assert p.subagents[0].delegation_description == "描述A"
