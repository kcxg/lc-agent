"""内置（框架自带）关联提示词：自动落库、只读、不自动绑定。"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from lc_agent.app import LcAgentApp
from lc_agent.db.builtin_prompts import sync_builtin_prompts
from lc_agent.db.engine import get_async_session, init_db, reset_engine
from lc_agent.db.models import AgentPromptBindingDB, PromptTemplateDB
from lc_agent.prompts import free_related_prompts as frp
from lc_agent.prompts.free_related_prompts import builtin_prompt_db_id, prompts_added_to_db
from lc_agent.tools.registry import ToolRegistry
from tests.conftest import setup_test_auth


@pytest.fixture(autouse=True)
async def setup(tmp_path):
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    await init_db(db_url)
    yield db_url
    ToolRegistry._global_tools = {}
    ToolRegistry._group_descriptions = {}
    ToolRegistry._instance = None
    reset_engine()


async def _prompt_rows(db_url) -> dict[str, tuple[str, str, str]]:
    """id → (name, content, source)。属性在会话内取，避免游离实例报错。"""
    async with get_async_session(db_url) as session:
        result = await session.execute(select(PromptTemplateDB))
        return {row.id: (row.name, row.content, row.source) for row in result.scalars().all()}


@pytest.mark.asyncio
async def test_sync_inserts_all_builtin_prompts_with_fixed_ids(setup):
    changed = await sync_builtin_prompts(setup)

    rows = await _prompt_rows(setup)
    assert changed == len(prompts_added_to_db)
    for prompt_cls in prompts_added_to_db:
        name, content, source = rows[builtin_prompt_db_id(prompt_cls)]
        assert name == prompt_cls.name
        assert content == prompt_cls.prompt
        assert source == "builtin"


@pytest.mark.asyncio
async def test_sync_is_idempotent(setup):
    await sync_builtin_prompts(setup)

    assert await sync_builtin_prompts(setup) == 0
    assert len(await _prompt_rows(setup)) == len(prompts_added_to_db)


@pytest.mark.asyncio
async def test_sync_refreshes_rows_changed_in_db(setup, monkeypatch):
    await sync_builtin_prompts(setup)
    target = frp.VibeCodingPrompt
    target_id = builtin_prompt_db_id(target)
    monkeypatch.setattr(target, "name", "改过的名字")
    monkeypatch.setattr(target, "prompt", "改过的正文")

    assert await sync_builtin_prompts(setup) == 1

    name, content, source = (await _prompt_rows(setup))[target_id]
    assert (name, content, source) == ("改过的名字", "改过的正文", "builtin")


@pytest.mark.asyncio
async def test_sync_does_not_touch_user_prompts(setup):
    async with get_async_session(setup) as session:
        session.add(PromptTemplateDB(id="user-1", name="我的提示词", content="我的内容"))
        await session.commit()

    await sync_builtin_prompts(setup)

    assert (await _prompt_rows(setup))["user-1"] == ("我的提示词", "我的内容", "user")


@pytest.mark.asyncio
async def test_sync_does_not_bind_prompts_to_any_agent(setup):
    await sync_builtin_prompts(setup)

    async with get_async_session(setup) as session:
        result = await session.execute(select(AgentPromptBindingDB))
        assert list(result.scalars().all()) == []


@pytest.fixture
async def app_and_headers(setup):
    config = {
        "provider": {"openai": {"base_url": "http://fake", "api_key": "sk-fake", "models": [{"model_id": "gpt-4", "raw_model_id": "gpt-4"}]}},
        "agent": {"default_model": "gpt-4", "system_prompt": "You are helpful."},
        "database": {"url": setup, "checkpoint_path": ":memory:"},
    }
    app = LcAgentApp(config)
    headers = await setup_test_auth(app.fastapi_app)
    return app, headers


@pytest.mark.asyncio
async def test_builtin_prompt_visible_to_users_but_read_only(app_and_headers, setup):
    app, headers = app_and_headers
    await sync_builtin_prompts(setup)
    builtin_id = builtin_prompt_db_id(frp.VibeCodingPrompt)
    transport = ASGITransport(app=app.fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/prompts", headers=headers)
        update_resp = await client.put(
            f"/api/prompts/{builtin_id}", json={"content": "试图改内置"}, headers=headers
        )
        delete_resp = await client.delete(f"/api/prompts/{builtin_id}", headers=headers)

    assert listed.status_code == 200
    item = next(p for p in listed.json() if p["id"] == builtin_id)
    assert item["source"] == "builtin"
    assert item["content"] == frp.VibeCodingPrompt.prompt

    assert update_resp.status_code == 403
    assert delete_resp.status_code == 403
    assert (await _prompt_rows(setup))[builtin_id][1] == frp.VibeCodingPrompt.prompt


@pytest.mark.asyncio
async def test_user_prompt_still_editable(app_and_headers):
    app, headers = app_and_headers
    transport = ASGITransport(app=app.fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/prompts", json={"name": "我的规范", "content": "原始内容"}, headers=headers
        )
        assert created.status_code == 201
        assert created.json()["source"] == "user"
        prompt_id = created.json()["id"]

        updated = await client.put(
            f"/api/prompts/{prompt_id}", json={"content": "改后内容"}, headers=headers
        )
        deleted = await client.delete(f"/api/prompts/{prompt_id}", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["content"] == "改后内容"
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_builtin_prompt_can_be_bound_by_user(app_and_headers, setup):
    """用户仍然需要自己勾选：绑定接口对内置提示词正常工作。"""
    app, headers = app_and_headers
    await sync_builtin_prompts(setup)
    builtin_id = builtin_prompt_db_id(frp.ForbidActionPrompt)
    transport = ASGITransport(app=app.fastapi_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bind_resp = await client.put(
            "/api/agents/chat/prompts", json={"prompt_ids": [builtin_id]}, headers=headers
        )
        bound_resp = await client.get("/api/agents/chat/prompts", headers=headers)

    assert bind_resp.status_code == 200
    assert bound_resp.json() == [builtin_id]


def _define_probe_subclass(*lines: str) -> None:
    """按给定类体逐行定义 AbstractFreeRelatedPrompts 的子类，用于验证护栏。"""
    source = "class Probe(AbstractFreeRelatedPrompts):\n" + "\n".join(
        f"    {line}" for line in lines
    )
    exec(source, {"AbstractFreeRelatedPrompts": frp.AbstractFreeRelatedPrompts})


def test_complete_subclass_defines_fine():
    _define_probe_subclass("key = 'test-complete'", "name = 'n'", "prompt = 'p'")


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(("name = 'n'", "prompt = 'p'"), id="missing-key"),
        pytest.param(("key = 'missing-name'", "prompt = 'p'"), id="missing-name"),
        pytest.param(("key = 'blank-prompt'", "name = 'n'", "prompt = '   '"), id="blank-prompt"),
    ],
)
def test_incomplete_subclass_fails_at_class_definition(lines):
    """纯注解不强制赋值，靠 __init_subclass__ 在类定义那一刻报错。"""
    with pytest.raises(TypeError):
        _define_probe_subclass(*lines)


def test_duplicate_key_fails_at_class_definition():
    """key 重复会落到同一条 DB 记录，后者静默覆盖前者 —— 必须拦住。"""
    _define_probe_subclass("key = 'test-duplicate'", "name = '第一个'", "prompt = 'p'")

    with pytest.raises(ValueError, match="重复"):
        _define_probe_subclass("key = 'test-duplicate'", "name = '第二个'", "prompt = 'p'")


def test_shipped_prompts_pass_the_guard():
    keys = [prompt_cls.key for prompt_cls in prompts_added_to_db]
    assert len(keys) == len(set(keys))
    assert all(cls.name.strip() and cls.prompt.strip() for cls in prompts_added_to_db)
