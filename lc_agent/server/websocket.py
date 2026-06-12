# lc_agent/server/websocket.py
import asyncio
import uuid
from typing import Any

from fastapi import WebSocket

from lc_agent.core.engine import AgentEngine


class ChatWebSocketHandler:
    """Handles WebSocket connections for streaming chat."""

    def __init__(self, engine: AgentEngine):
        self.engine = engine
        self.active_connections: dict[str, WebSocket] = {}
        self._message_counts: dict[str, int] = {}

    async def connect(self, websocket: WebSocket, thread_id: str | None = None) -> str:
        """Accept WebSocket connection."""
        await websocket.accept()
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        self.active_connections[thread_id] = websocket
        await websocket.send_json({"type": "connected", "thread_id": thread_id})
        return thread_id

    async def disconnect(self, thread_id: str):
        """Clean up on disconnect."""
        self.active_connections.pop(thread_id, None)

    async def handle_message(self, websocket: WebSocket, thread_id: str, data: dict):
        """Process incoming message and stream response."""
        msg_type = data.get("type", "message")

        if msg_type == "message":
            content = data.get("content", "")
            preset_id = data.get("preset_id", "__chat__")
            try:
                async for event in self.engine.chat_stream(content, thread_id, preset_id):
                    await self._send_event(websocket, event)
                await websocket.send_json({"type": "done"})

                self._message_counts[thread_id] = self._message_counts.get(thread_id, 0) + 1
                if self._message_counts[thread_id] == 1:
                    asyncio.create_task(
                        self._generate_and_push_title(websocket, thread_id, content, preset_id)
                    )
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

        elif msg_type == "interrupt_response":
            approved = data.get("approved", False)
            preset_id = data.get("preset_id", "__chat__")
            try:
                from langgraph.types import Command

                agent = self.engine._agents.get(preset_id)
                if agent is None:
                    await websocket.send_json({"type": "error", "message": "No agent found for resume"})
                    return

                config = {"configurable": {"thread_id": thread_id}}
                resume_value = {"approved": approved}

                async for event in agent.astream_events(
                    Command(resume=resume_value),
                    config=config,
                    version="v2",
                ):
                    await self._send_event(websocket, event)
                await websocket.send_json({"type": "done"})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    async def _generate_and_push_title(self, websocket: WebSocket, thread_id: str, first_message: str, preset_id: str = "__chat__"):
        """Generate title from first message using the agent's model, save to DB, and push to client."""
        try:
            model_id = ""
            if preset_id in self.engine.BUILTIN_IDS:
                for bp in self.engine.get_builtin_presets():
                    if bp.id == preset_id:
                        model_id = bp.default_model
                        break
            else:
                preset = self.engine._presets.get(preset_id) or self.engine._custom_presets.get(preset_id)
                if preset:
                    model_id = preset.default_model
            title = await self.engine.generate_title(first_message, model_id)

            from lc_agent.db.engine import get_async_session
            from lc_agent.db.repository import SessionRepository
            session = get_async_session()
            try:
                repo = SessionRepository(session)
                await repo.update(thread_id, title=title)
            finally:
                await session.close()

            await websocket.send_json({"type": "title_update", "thread_id": thread_id, "title": title})
        except Exception as e:
            print(f"[WS] Title generation failed: {e}")

    async def _send_event(self, websocket: WebSocket, event: dict):
        """Convert LangGraph astream_events v2 to client-friendly format."""
        kind = event.get("event", "")

        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                await websocket.send_json({"type": "token", "content": chunk.content})

        elif kind == "on_tool_start":
            tool_input = event.get("data", {}).get("input", {})
            await websocket.send_json({
                "type": "tool_call",
                "name": event.get("name", ""),
                "run_id": event.get("run_id", ""),
                "args": tool_input,
            })

        elif kind == "on_tool_end":
            output = event.get("data", {}).get("output", "")
            await websocket.send_json({
                "type": "tool_result",
                "name": event.get("name", ""),
                "result": str(output)[:2000],
            })

        elif kind == "on_chain_end":
            data_output = event.get("data", {}).get("output", {})
            if isinstance(data_output, dict) and "__interrupt" in str(data_output):
                await websocket.send_json({
                    "type": "interrupt",
                    "message": "Tool requires approval",
                    "data": data_output,
                })
