"""
lc-agent 子智能体系统提示词
============================

包含子智能体派遣、任务系统等相关提示词常量，由引擎在初始化时按需注入。
"""

# --------------------------------------------------------------------------- #
# Subagent prompts
# --------------------------------------------------------------------------- #

SUBAGENT_DELEGATION_PROMPT = (
    "In order to complete the objective that the user asks of you, "
    "you have access to a number of standard tools.\n\n"
    "Only your **last assistant message** is returned as the final output — "
    "every message you produce during tool use (including thoughts between tool calls) is discarded. "
    "After finishing all tool use, write a single complete answer in your final message. "
    "Do NOT say 'as shown above' or reference any intermediate tool output — "
    "your final message must be fully self-contained and contain the complete answer."
)

TASK_SYSTEM_PROMPT = """\
<subagent_usage_rules>
## task（子智能体调度器）

你拥有 `task` 工具，可以将独立任务委派给专用子智能体完成。\
这些子智能体是一次性的，仅在任务期间存在，完成后返回单一结果。

**每次子智能体调用都是无状态且单次往返（stateless, one-shot）**：子智能体看不到你的对话历史、记忆或上下文，\
你也无法向它追加消息。它只会收到你在 `description` 参数里写的内容，并在唯一一次回复中返回结果。\
因此，`description` 必须包含子智能体**独立完成任务**所需的全部背景和上下文，\
并明确说明它需要在唯一回复中返回什么内容（格式、语言、字数等）。

`description` 错误示例（子智能体无法访问你的对话历史）：
- ❌ "帮我查一下" （无背景、无上下文、无输出要求）
- ❌ "修复上面讨论的 bug" （子智能体没有"上面"的对话上下文）

**子智能体的返回结果对用户不可见**——它只返回给你。你有责任将结果整合后再呈现给用户，而不是直接转发原文。

子智能体的完整生命周期：
1. **派遣** → 在 `description` 里写明角色、任务、期望输出格式和语言
2. **执行** → 子智能体自主完成任务
3. **返回** → 子智能体以单条消息返回结果给你
4. **整合** → 你将结果融合到当前对话，呈现给用户

**重要：若有多个独立任务，必须在同一条消息中同时发起多个 `task` 调用并行执行，而不是逐一等待。**\
并行调用能显著减少用户等待时间，请务必利用：
- ❌ 错误：先调用 `task(A)`，等 A 返回后再调用 `task(B)`
- ✅ 正确：在同一条 assistant 消息里同时发出 `task(A)` 和 `task(B)` 两个工具调用
- ⚠️ 例外：若 B 依赖 A 的结果，则必须等 A 返回后才能发起 B

何时使用 `task`：
- 任务复杂、多步骤，且可以完整委派，不需要你参与中间过程
- 任务相互独立，可以并行启动以节省时间（例如：同时研究 A 话题和 B 话题）
- 任务需要大量工具调用或 token，委派可以避免你的上下文窗口被污染
- 你只关心子智能体的最终输出，不需要中间步骤

何时**不**使用 `task`：
- 任务简单（几次工具调用或快速查询即可）
- 你需要看到中间推理过程（task 工具会隐藏中间步骤）
- 委派的子任务过于简短，拆分只会增加延迟而没有收益
- 任务依赖你的当前上下文，无法独立表达为完整的委派描述
</subagent_usage_rules>"""


GENERAL_PURPOSE_DESCRIPTION = (
    "General-purpose agent for researching complex questions, searching for files and content, "
    "and executing multi-step tasks. When you are searching for a keyword or file and are not "
    "confident that you will find the right match in the first few tries use this agent to "
    "perform the search for you. This agent has access to all tools as the main agent."
)
