# lc_agent/app.py
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from langchain_agentskills import SkillsToolkit
from langchain_agentskills.loaders import CompositeSkillLoader, DirectorySkillLoader

from lc_agent.core.auth import AuthService
from lc_agent.core.engine import AgentEngine
from lc_agent.core.permissions import PermissionsService
from lc_agent.db.engine import init_db
from lc_agent.mcp.manager import McpManager
from lc_agent.server.app import create_app, mount_static_files
from lc_agent.server import sse as sse_module
from lc_agent.skills.filtered_loader import FilteredSkillLoader


class LcAgentApp:
    """Main application orchestrator — creates engine, server, and runs."""

    def __init__(self, config: dict, host: str = "127.0.0.1", port: int = 8000):
        self.config = config
        self.host = host
        self.port = port
        self._db_url = config.get("database", {}).get("url", "sqlite+aiosqlite:///./lc_agent_data.db")
        self._checkpoint_path = config.get("database", {}).get("checkpoint_path", "./lc_agent_checkpoints.db")
        permissions_path = config.get("permissions", {}).get("path", "./permissions.jsonc")
        self._permissions_service = PermissionsService(permissions_path=Path(permissions_path))
        self.engine = AgentEngine(config)
        skills_dirs = config.get("skills", ["./skills"])
        existing_dirs = [d for d in skills_dirs if Path(d).is_dir()]
        if existing_dirs:
            inner_loaders = [DirectorySkillLoader(d) for d in existing_dirs]
            inner = inner_loaders[0] if len(inner_loaders) == 1 else CompositeSkillLoader(inner_loaders)
            self.filtered_loader = FilteredSkillLoader(inner)
            self.skills_toolkit = SkillsToolkit(loaders=[self.filtered_loader])
        else:
            self.filtered_loader = None
            self.skills_toolkit = None
        mcp_config = config.get("mcp_servers", {})
        self.mcp_manager = McpManager(mcp_config, on_state_change=self._on_mcp_state_change)
        self.fastapi_app = create_app(config, lifespan=self._lifespan)
        self.fastapi_app.state.mcp_manager = self.mcp_manager
        self.fastapi_app.state.skills_toolkit = self.skills_toolkit
        self.fastapi_app.state.filtered_loader = self.filtered_loader
        self.engine._skills_toolkit = self.skills_toolkit
        self.engine._mcp_manager = self.mcp_manager
        self.fastapi_app.state.engine = self.engine
        self.fastapi_app.state.permissions = self._permissions_service
        self.engine._permissions_service = self._permissions_service
        # JWT auth service (replaces old cookie-based auth)
        auth_config = config.get("auth", {})
        if auth_config.get("enabled", False):
            auth_secret = auth_config.get("secret", "")
            if len(auth_secret) >= 16:
                self.fastapi_app.state.auth_service = AuthService(
                    secret=auth_secret,
                    token_expire_days=auth_config.get("token_expire_days", 7),
                )
            else:
                print("[Auth] WARNING: auth.enabled=true but secret is too short (<16 chars), auth disabled")
        sse_module.configure(self.engine, self._db_url)
        mount_static_files(self.fastapi_app)

    def _on_mcp_state_change(self):
        self.engine._mcp_generation += 1

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """FastAPI lifespan: startup and shutdown logic."""
        import asyncio

        await init_db(self._db_url)
        # Ensure default admin user exists if auth is enabled
        await self._ensure_default_admin()
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
            import aiosqlite
            conn = await aiosqlite.connect(self._checkpoint_path)
            saver = AsyncSqliteSaver(conn)
            await saver.setup()
            self.engine._checkpointer = saver
        except Exception as e:
            print(f"[Warning] Checkpoint saver setup failed, using None: {e}")

        await self._load_presets_from_db()

        async def _connect_mcp_background():
            try:
                await self.mcp_manager.connect_all()
                connected = [s for s in self.mcp_manager.servers if s.status == "connected"]
                if connected:
                    print(f"[MCP] Connected: {[s.name for s in connected]}")
            except Exception as e:
                print(f"[MCP] Background connection error: {e}")

        asyncio.create_task(_connect_mcp_background())
        try:
            yield
        finally:
            await self.mcp_manager.shutdown()

    async def _load_presets_from_db(self):
        """Load user-created presets from database on startup."""
        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models import AgentPresetDB
        from lc_agent.core.models import AgentPreset
        from sqlalchemy import select

        session = get_async_session(self._db_url)
        try:
            stmt = select(AgentPresetDB)
            result = await session.execute(stmt)
            for row in result.scalars().all():
                preset = AgentPreset(
                    id=row.id,
                    name=row.name,
                    system_prompt=row.system_prompt,
                    default_model=row.default_model,
                    allowed_tool_groups=row.allowed_tool_groups,
                    allowed_mcp_servers=row.allowed_mcp_servers,
                    allowed_skills=row.allowed_skills,
                )
                self.engine._presets[preset.id] = preset
            loaded = len(self.engine._presets)
            if loaded:
                print(f"[Agents] Loaded {loaded} user presets from database")
        except Exception as e:
            print(f"[Warning] Failed to load presets from DB: {e}")
        finally:
            await session.close()

    async def _ensure_default_admin(self):
        """Create default admin user if auth is enabled and no users exist."""
        auth_service = getattr(self.fastapi_app.state, "auth_service", None)
        if auth_service is None:
            return

        from lc_agent.db.engine import get_async_session
        from lc_agent.db.models_auth import User
        from sqlalchemy import select

        auth_config = self.config.get("auth", {})
        default_username = auth_config.get("admin_username", "admin")
        default_password = auth_config.get("admin_password", "admin123")

        session = get_async_session(self._db_url)
        try:
            result = await session.execute(select(User).limit(1))
            if result.first() is not None:
                return  # Users already exist

            user = User(
                username=default_username,
                password_hash=auth_service.hash_password(default_password),
                role="admin",
            )
            session.add(user)
            await session.commit()
            print(f"[Auth] Created default admin user: {default_username}")
        except Exception as e:
            print(f"[Warning] Failed to create default admin: {e}")
        finally:
            await session.close()

    def add_agent(self, name: str, graph, description: str = ""):
        """Register a pre-built CompiledStateGraph as a named agent.

        Args:
            name: Unique agent identifier
            graph: A compiled LangGraph (must have ainvoke and astream_events)
            description: Human-readable description
        """
        if name in self.engine._agents:
            raise ValueError(f"Agent '{name}' already registered")

        from lc_agent.core.models import AgentPreset

        self.engine._agents[name] = graph
        self.engine._agent_mcp_gen[name] = self.engine._mcp_generation
        preset = AgentPreset(
            id=name,
            name=name,
            system_prompt=description or f"Custom agent: {name}",
            default_model="custom",
            source="code",
        )
        self.engine._custom_presets[name] = preset

    def run(self):
        """Start the server (blocking)."""
        from lc_agent import __version__

        print(f"\n  lc_agent v{__version__}")
        print(f"  Web UI: http://{self.host}:{self.port}")
        print(f"  API Docs: http://{self.host}:{self.port}/api/docs\n")
        uvicorn.run(self.fastapi_app, host=self.host, port=self.port)
