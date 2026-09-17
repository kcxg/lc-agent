/**
 * Agent 身份图标（emoji）。
 * 顶栏选择器、侧栏会话分组、标签栏下拉共用同一套，
 * 避免同一个 Agent 在三处显示不同图标。
 *
 * project_mode 优先于 source：项目模式是身份标识，比「代码/内置」更能说明这个 Agent 是什么。
 */
export function getAgentIcon(
  agent: { id: string; source: string; project_mode?: boolean } | null,
): string {
  if (!agent) return '🤖'
  if (agent.project_mode) return '📁'
  if (agent.source === 'code') return '⚙️'
  if (agent.id === 'chat') return '💬'
  if (agent.id === 'empty') return '🧩'
  if (agent.source === 'builtin') return '✨'
  return '🤖'
}
