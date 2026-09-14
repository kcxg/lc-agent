/**
 * 工具调用入参的展示过滤。
 *
 * MCP 里没有参数的工具，历史版本会被后端塞一个占位参数 placeholder，
 * 模型于是照着它编一个值（"{}"、"no params" 之类），在界面上显示成一条假的入参。
 * 后端已经不再产生这个参数了，这里再挡一道，让数据库里已有的历史消息也干净。
 *
 * 入参区、折叠态的标题摘要、复制成 Markdown 三处共用这一个判断。
 */

/** 不展示的入参名（占位参数） */
export const HIDDEN_ARG_KEYS: ReadonlySet<string> = new Set(['placeholder'])

/** 这个入参该不该展示 */
export function isHiddenArg(key: string): boolean {
  return HIDDEN_ARG_KEYS.has(key)
}

/** 过滤掉占位参数后的入参列表，保持原来的顺序 */
export function visibleArgEntries(args: Record<string, unknown> | null | undefined): [string, unknown][] {
  if (!args || typeof args !== 'object') return []
  return Object.entries(args).filter(([key]) => !isHiddenArg(key))
}
