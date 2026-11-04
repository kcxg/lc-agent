"""直播消息的权威轮次号：后端在流开头下发 conversation_round 事件。

背景：前端原本自己数轮次（历史消息用接口给的号、直播消息本地 +1），
本地列表一旦被整体替换/截断（或该轮不是本客户端发的），计数器就永久落后，
「N 个文件已更改」卡片会被 last-write-wins 顶到别的轮次的消息上。
现在改为后端下发轮次号、前端回填到每条直播消息上，前端不再自己数。
"""
import json
from pathlib import Path

from lc_agent.server.stream_utils import format_sse_event

SSE_PY = Path(__file__).resolve().parents[1] / "lc_agent" / "server" / "sse.py"


def _parse_frame(frame: str) -> tuple[str, dict]:
    lines = frame.strip().split("\n")
    return lines[0].removeprefix("event: "), json.loads(lines[1].removeprefix("data: "))


def test_conversation_round_frame_shape():
    frame = format_sse_event("conversation_round", {"thread_id": "t1", "round_number": 112})
    event, data = _parse_frame(frame)
    assert event == "conversation_round"
    assert data["type"] == "conversation_round"
    assert data["round_number"] == 112
    assert data["thread_id"] == "t1"
    assert frame.endswith("\n\n")


def test_conversation_round_emitted_on_both_paths():
    """主对话流与续跑（resume）流都必须下发：
    少一条，那条路径的直播消息就会退回本地计数，问题复现。"""
    src = SSE_PY.read_text(encoding="utf-8")
    assert src.count('format_sse_event("conversation_round"') == 2


def test_round_number_comes_from_user_message_count():
    """口径必须是「含本轮 user 消息的序号」，与 FileChange.round_number 同源。"""
    src = SSE_PY.read_text(encoding="utf-8")
    assert src.count("await persistence.get_session_user_message_count(thread_id)") >= 2
    assert 'bind_session_for_file_tracking(thread_id, round_number=round_number)' in src
