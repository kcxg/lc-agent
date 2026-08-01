"""
lc-agent Todo 工具提示词
=========================

包含 write_todos 工具的 system prompt 和 tool description，
由引擎在 preset 启用 todo 功能时注入。
"""
from langchain.agents.middleware.todo import WRITE_TODOS_SYSTEM_PROMPT, WRITE_TODOS_TOOL_DESCRIPTION

TODO_FINAL_ANSWER_GUARD = """## Final Answer Guard for `write_todos`

- Do not create todo items whose only purpose is to write, organize, summarize, or deliver the final answer.
- Before writing the substantive final answer to the user, make your last necessary `write_todos` call.
- After you start writing the substantive final answer, do not call `write_todos` again in the same turn.
- If the only remaining todo is about producing the final answer, do not call `write_todos` just to mark it complete. Deliver the final answer directly.
"""

TODO_SYSTEM_PROMPT = f"<todo_usage_rules>\n{WRITE_TODOS_SYSTEM_PROMPT}\n\n{TODO_FINAL_ANSWER_GUARD}\n</todo_usage_rules>"
TODO_TOOL_DESCRIPTION = f"{WRITE_TODOS_TOOL_DESCRIPTION}\n\n{TODO_FINAL_ANSWER_GUARD}"
