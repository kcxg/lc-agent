import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const panePath = join(root, 'src', 'components', 'panels', 'FileEditorPane.vue')
const pane = readFileSync(panePath, 'utf8')
const errorModulePath = join(root, 'src', 'components', 'panels', 'documentPreviewError.ts')
const errorModule = readFileSync(errorModulePath, 'utf8')
const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}

function expectNotIncludes(name, content, unexpected) {
  if (content.includes(unexpected)) failures.push(`${name} 不应再包含: ${unexpected}`)
}

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

function expectEqual(name, actual, expected) {
  if (actual !== expected) failures.push(`${name} 期望 ${expected}，实际 ${actual}`)
}

// 四类文档各自有独立的懒加载入口，缺一个就会有格式打不开
for (const kind of ['pdf', 'docx', 'xlsx', 'pptx']) {
  expectMatch('FileEditorPane.vue', pane, new RegExp(`^\\s*${kind}:`, 'm'), `缺少 ${kind} 的预览组件懒加载入口`)
}

// 渲染失败必须回传，否则界面上只会留下空白
expectIncludes('FileEditorPane.vue', pane, '@error="onDocumentError"')

// 异常文案的映射逻辑集中在 documentPreviewError.ts，面板只负责调用
expectIncludes('FileEditorPane.vue', pane, "from '@/components/panels/documentPreviewError'")
expectIncludes('FileEditorPane.vue', pane, 'docError.value = documentErrorMessage(')
expectIncludes('FileEditorPane.vue', pane, "console.warn('[document-preview] render failed:'")
// 映射规则不得回流到面板里，否则两处定义会各自漂移
expectNotIncludes('FileEditorPane.vue', pane, 'DOC_RENDER_ERROR_HINTS')
expectNotIncludes('FileEditorPane.vue', pane, "reading 'anchors'")
expectNotIncludes('FileEditorPane.vue', pane, "reading 'comments'")

// 模块静态结构
expectIncludes('documentPreviewError.ts', errorModule, 'DOC_RENDER_ERROR_HINTS')
expectIncludes('documentPreviewError.ts', errorModule, "reading 'anchors'")
expectIncludes('documentPreviewError.ts', errorModule, "reading 'comments'")

// 直接执行映射逻辑，确认特征命中与兜底都真的生效
let documentErrorMessage
try {
  ;({ documentErrorMessage } = await import(pathToFileURL(errorModulePath).href))
} catch (e) {
  failures.push(`documentPreviewError.ts 无法执行: ${e.message}`)
}

if (typeof documentErrorMessage === 'function') {
  const anchors = documentErrorMessage(new TypeError("Cannot read properties of undefined (reading 'anchors')"))
  expectEqual('anchors 文案', anchors, '该表格包含图表或图片，其绘图信息无法被预览组件解析，暂不支持预览。')

  const comments = documentErrorMessage(new TypeError("Cannot read properties of undefined (reading 'comments')"))
  expectEqual('comments 文案', comments, '该表格包含批注，其批注信息无法被预览组件解析，暂不支持预览。')

  // 未知异常保留原始信息，便于继续定位
  const unknown = documentErrorMessage(new Error('boom'))
  expectEqual('未知异常文案', unknown, '文档渲染失败：boom')

  // 非 Error 入参不能反过来把预览面板打挂
  expectEqual('字符串入参文案', documentErrorMessage('plain text'), '文档渲染失败：plain text')
} else {
  failures.push('documentPreviewError.ts 未导出 documentErrorMessage 函数')
}

if (failures.length > 0) {
  console.error('文档预览契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('文档预览契约测试通过')
