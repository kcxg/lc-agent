from pathlib import Path

import pytest
from pydantic import ValidationError

from lc_agent.config.loader import load_config_from_file, substitute_env_vars
from lc_agent.config.schema import AppConfig
from lc_agent.tools.system_tools._config import (
    set_active_project,
    validate_path_access,
    validate_read_path,
    validate_write_path,
)


@pytest.fixture(autouse=True)
def _reset_active_project():
    """Ensure ContextVar is cleared after each test to prevent state leakage."""
    yield
    set_active_project(None)


class TestSubstituteEnvVars:
    def test_replaces_env_var(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "sk-12345")
        result = substitute_env_vars({"key": "{env:TEST_API_KEY}"})
        assert result == {"key": "sk-12345"}

    def test_leaves_non_env_strings_unchanged(self):
        result = substitute_env_vars({"key": "plain-value"})
        assert result == {"key": "plain-value"}

    def test_handles_nested_dicts(self, monkeypatch):
        monkeypatch.setenv("NESTED_VAL", "secret")
        data = {"outer": {"inner": "{env:NESTED_VAL}"}}
        result = substitute_env_vars(data)
        assert result == {"outer": {"inner": "secret"}}

    def test_handles_lists(self, monkeypatch):
        monkeypatch.setenv("LIST_VAL", "item")
        data = {"items": ["{env:LIST_VAL}", "static"]}
        result = substitute_env_vars(data)
        assert result == {"items": ["item", "static"]}

    def test_missing_env_var_raises(self):
        with pytest.raises(ValueError, match="Environment variable 'NONEXISTENT' not found"):
            substitute_env_vars({"key": "{env:NONEXISTENT}"})


class TestLoadConfigFromFile:
    def test_loads_jsonc_file(self, tmp_path):
        config_file = tmp_path / "config.jsonc"
        config_file.write_text(
            """{
            // This is a comment
            "agent": {
                "system_prompt": "Hello",
                "default_model": "test-model",
                "streaming": true
            },
            "provider": {
                "default": {
                    "api_key": "sk-test",
                    "base_url": "https://api.example.com/v1",
                    "models": [{"id": "test-model", "context_limit": 8000}]
                }
            },
            "mcp": {},
            "session": {"db_path": ":memory:"}
        }"""
        )
        config = load_config_from_file(str(config_file))
        assert config["agent"]["system_prompt"] == "Hello"

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config_from_file("/nonexistent/path/config.jsonc")

    def test_example_loads_when_auth_is_disabled_without_auth_env(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.delenv("LC_AGENT_ADMIN_PASSWORD", raising=False)
        monkeypatch.delenv("LC_AGENT_SESSION_SECRET", raising=False)

        example_path = Path(__file__).parents[1] / "config.example.jsonc"

        config = load_config_from_file(str(example_path))

        assert config["auth"]["enabled"] is False
        assert config["auth"]["admin_password"] == ""
        assert config["auth"]["session_secret"] == ""


def test_memory_api_key_uses_env_placeholder(monkeypatch, tmp_path):
    from lc_agent.config.loader import load_config_from_file

    monkeypatch.setenv("NBRAG_API_KEY", "env-secret")
    config_path = tmp_path / "config.jsonc"
    config_path.write_text(
        """
        {
          "memory": {
            "semantic_search": {
              "api_key": "{env:NBRAG_API_KEY}"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    config = load_config_from_file(str(config_path))

    assert config["memory"]["semantic_search"]["api_key"] == "env-secret"


def test_memory_api_key_keeps_literal_value(tmp_path):
    from lc_agent.config.loader import load_config_from_file

    config_path = tmp_path / "config.jsonc"
    config_path.write_text(
        """
        {
          "memory": {
            "semantic_search": {
              "api_key": "literal-secret"
            }
          }
        }
        """,
        encoding="utf-8",
    )

    config = load_config_from_file(str(config_path))

    assert config["memory"]["semantic_search"]["api_key"] == "literal-secret"


def test_memory_defaults_use_durable_sqlite_store():
    from lc_agent.config.schema import AppConfig

    config = AppConfig()

    assert config.memory.enabled is True
    assert config.memory.type == "sqlite"
    assert config.memory.path == "./lc_agent_memory.db"
    assert config.memory.save_policy == "explicit"
    assert config.memory.retrieval_policy == "manual"
    assert config.memory.semantic_search.enabled is True
    assert config.memory.semantic_search.api_key == "{env:NBRAG_API_KEY}"
    assert config.memory.semantic_search.base_url == "https://api.siliconflow.cn/v1"
    assert config.memory.semantic_search.model == "BAAI/bge-m3"
    assert config.memory.semantic_search.dims == 1024


class TestAppConfig:
    def test_validates_minimal_config(self):
        config = AppConfig(
            provider={"default": {"api_key": "sk-test", "base_url": "https://api.example.com/v1", "models": [{"id": "m1", "context_limit": 4000}]}},
            agent={"system_prompt": "Hi", "default_model": "m1", "streaming": True},
        )
        assert config.agent["default_model"] == "m1"

    def test_mcp_server_url_defaults_to_http(self):
        config = AppConfig(mcpServers={"remote": {"url": "http://localhost:3000/mcp"}})
        assert config.mcpServers["remote"].type == "http"

    def test_rejects_missing_agent_section(self):
        with pytest.raises(ValidationError):
            AppConfig(agent="not a dict")


class TestValidatePathAccess:
    def test_relative_path_resolves_to_active_project_root(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        subdir = project_root / "src"
        subdir.mkdir()

        set_active_project(str(project_root))
        resolved = validate_path_access("src", allowed_directories=[str(project_root)])

        assert resolved == str(subdir)

    def test_dot_path_resolves_to_active_project_root(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()

        set_active_project(str(project_root))
        resolved = validate_path_access(".", allowed_directories=[str(project_root)])

        assert resolved == str(project_root)

    def test_absolute_path_still_allowed(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        other = tmp_path / "other"
        other.mkdir()

        set_active_project(str(project_root))
        resolved = validate_path_access(str(other), allowed_directories=[str(tmp_path)])

        assert resolved == str(other)

    def test_no_active_project_falls_back_to_cwd_resolution(self, tmp_path):
        target = tmp_path / "fallback"
        target.mkdir()

        set_active_project(None)
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            resolved = validate_path_access("fallback", allowed_directories=[str(tmp_path)])
            assert resolved == str(target)
        finally:
            os.chdir(original_cwd)

    def test_outside_allowed_directories_raises(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        set_active_project(str(project_root))
        with pytest.raises(PermissionError):
            validate_path_access(str(outside), allowed_directories=[str(project_root)])


class TestValidateReadWritePath:
    def test_validate_read_path_uses_active_project_root(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        file_path = project_root / "readme.txt"
        file_path.write_text("hello")

        set_active_project(str(project_root))
        resolved = validate_read_path("readme.txt")

        assert resolved == str(file_path)

    def test_validate_write_path_uses_active_project_root(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()

        set_active_project(str(project_root))
        resolved = validate_write_path("new_file.py")

        assert resolved == str(project_root / "new_file.py")
