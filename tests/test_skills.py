import pytest
from httpx import ASGITransport, AsyncClient

from lc_agent.app import LcAgentApp
from lc_agent.db.engine import init_db, reset_engine
from lc_agent.skills.scanner import SkillScanner
from lc_agent.skills.skill_middleware import _build_skills_prompt
from tests.conftest import setup_test_auth

@pytest.fixture
def skills_dir(tmp_path):
    skill1 = tmp_path / "coding" / "SKILL.md"
    skill1.parent.mkdir()
    skill1.write_text(
        "---\nname: coding-assistant\ndescription: Expert coding help\n---\n\n# Coding\n\nYou write clean code.\n",
        encoding="utf-8",
    )

    skill2 = tmp_path / "research" / "SKILL.md"
    skill2.parent.mkdir()
    skill2.write_text(
        "---\nname: researcher\ndescription: Deep research\n---\n\n# Research\n\nYou research thoroughly.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_scan_skills(skills_dir):
    scanner = SkillScanner(str(skills_dir))
    skills = scanner.scan()
    assert len(skills) == 2
    names = [s.name for s in skills]
    assert "coding-assistant" in names
    assert "researcher" in names


def test_skill_content(skills_dir):
    scanner = SkillScanner(str(skills_dir))
    scanner.scan()
    skill = scanner.get_by_name("coding-assistant")
    assert skill is not None
    assert "clean code" in skill.content
    assert skill.description == "Expert coding help"


def test_filter_skills(skills_dir):
    scanner = SkillScanner(str(skills_dir))
    scanner.scan()

    all_skills = scanner.get_filtered(None)
    assert len(all_skills) == 2

    no_skills = scanner.get_filtered([])
    assert len(no_skills) == 0

    some = scanner.get_filtered(["researcher"])
    assert len(some) == 1
    assert some[0].name == "researcher"


def test_skill_prompt_supports_direct_slash_commands():
    skill = type("Skill", (), {
        "name": "coding-assistant",
        "description": "Expert coding help",
    })()

    prompt = _build_skills_prompt([skill])

    assert "standalone `/`" in prompt
    assert "/coding-assistant" in prompt
    assert "call `load_skill`" in prompt


def test_empty_directory(tmp_path):
    scanner = SkillScanner(str(tmp_path / "nonexistent"))
    skills = scanner.scan()
    assert len(skills) == 0


@pytest.fixture
async def app_with_skills(skills_dir, tmp_path):
    reset_engine()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'auth.db'}"
    await init_db(db_url)

    config = {
        "provider": {
            "openai": {
                "base_url": "http://fake",
                "api_key": "sk-fake",
                "models": [{"id": "gpt-4"}],
            }
        },
        "agent": {"default_model": "gpt-4", "system_prompt": "You are helpful."},
        "skills": [str(skills_dir)],
        "database": {"url": db_url, "checkpoint_path": ":memory:"},
    }
    app = LcAgentApp(config)
    headers = await setup_test_auth(app.fastapi_app, db_url)
    yield app, headers
    reset_engine()

@pytest.mark.asyncio
async def test_toggle_skill_increments_mcp_generation(app_with_skills):
    app, headers = app_with_skills
    transport = ASGITransport(app=app.fastapi_app)
    gen_before = app.engine._mcp_generation

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/skills/coding-assistant/toggle", headers=headers)

    assert resp.status_code == 200
    assert app.engine._mcp_generation == gen_before + 1
