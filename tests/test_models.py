from lc_agent.core.models import AgentPreset


def test_agent_preset_subagent_ids_defaults_to_none():
    p = AgentPreset(id="x", name="n", system_prompt="s", default_model="m")
    assert p.subagent_ids is None


def test_agent_preset_subagent_ids_accepts_list():
    p = AgentPreset(id="x", name="n", system_prompt="s", default_model="m",
                    subagent_ids=["a", "b"])
    assert p.subagent_ids == ["a", "b"]
