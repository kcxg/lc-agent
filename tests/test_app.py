from lc_agent.app import LcAgentApp
from lc_agent.db.engine import get_async_session, init_db, reset_engine
from lc_agent.db.models import AgentPresetDB


class TestLcAgentApp:
    def test_creates_with_config(self, sample_config):
        app = LcAgentApp(sample_config)
        assert app.config == sample_config

    def test_has_fastapi_app(self, sample_config):
        app = LcAgentApp(sample_config)
        assert app.fastapi_app is not None

    def test_has_engine(self, sample_config):
        app = LcAgentApp(sample_config)
        assert app.engine is not None

    def test_default_host_and_port(self, sample_config):
        app = LcAgentApp(sample_config)
        assert app.host == "127.0.0.1"
        assert app.port == 8000

    def test_custom_host_and_port(self, sample_config):
        app = LcAgentApp(sample_config, host="0.0.0.0", port=9000)
        assert app.host == "0.0.0.0"
        assert app.port == 9000

    def test_add_agent_supports_delegation_description(self, sample_config):
        app = LcAgentApp(sample_config)
        graph = object()

        app.add_agent(
            name="funboost智能体",
            graph=graph,
            description="Funboost 专家",
            delegation_description="当你需要查询 funboost 知识时调用它",
        )

        preset = app.engine._custom_presets["funboost智能体"]
        assert preset.default_delegation_description == "当你需要查询 funboost 知识时调用它"


@pytest.mark.asyncio
async def test_load_presets_from_db_preserves_general_purpose_subagent_flag(tmp_path, sample_config):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    await init_db(db_url)

    session = get_async_session(db_url)
    try:
        session.add(AgentPresetDB(
            id="delegating-agent",
            name="Delegating Agent",
            system_prompt="Delegate when useful.",
            default_model="gpt-4",
            enable_general_purpose_subagent=True,
        ))
        await session.commit()
    finally:
        await session.close()

    app = LcAgentApp({**sample_config, "database": {"url": db_url}})
    await app._load_presets_from_db()

    assert app.engine._presets["delegating-agent"].enable_general_purpose_subagent is True
    reset_engine()


@pytest.mark.asyncio
async def test_load_presets_from_db_uses_subagents_structure(tmp_path, sample_config):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    await init_db(db_url)

    session = get_async_session(db_url)
    try:
        session.add(AgentPresetDB(
            id="delegating-agent",
            name="Delegating Agent",
            system_prompt="Delegate when useful.",
            default_model="gpt-4",
            subagents=[
                {
                    "agent_id": "child-agent",
                    "delegation_description": "当你需要查询 funboost 知识时调用它",
                }
            ],
        ))
        await session.commit()
    finally:
        await session.close()

    app = LcAgentApp({**sample_config, "database": {"url": db_url}})
    await app._load_presets_from_db()

    preset = app.engine._presets["delegating-agent"]
    assert preset.subagents is not None
    assert preset.subagents[0].agent_id == "child-agent"
    assert preset.subagents[0].delegation_description == "当你需要查询 funboost 知识时调用它"
    reset_engine()
