// 预览组件按标签名前缀字面匹配解析部分 OOXML 部件，遇到不认识的写法会抛出原始
// TypeError。这类报错对用户没有可读性，按已知特征转成明确说明；其余异常保留原文便于定位。

export interface DocumentRenderErrorHint {
  pattern: RegExp
  message: string
}

export const DOC_RENDER_ERROR_HINTS: DocumentRenderErrorHint[] = [
  {
    pattern: /reading 'anchors'/,
    message: '该表格包含图表或图片，其绘图信息无法被预览组件解析，暂不支持预览。',
  },
  {
    pattern: /reading 'comments'/,
    message: '该表格包含批注，其批注信息无法被预览组件解析，暂不支持预览。',
  },
]

export function documentErrorMessage(err: unknown): string {
  const raw = (err as { message?: string } | null | undefined)?.message || String(err)
  const hint = DOC_RENDER_ERROR_HINTS.find((item) => item.pattern.test(raw))
  return hint ? hint.message : `文档渲染失败：${raw}`
}
