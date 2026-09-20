import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = (p) => readFileSync(join(root, p), 'utf8')

const failures = []

function expect(cond, message) {
  if (!cond) failures.push(message)
}

const ui = read('src/stores/ui.ts')
const sidebar = read('src/components/layout/LeftSidebar.vue')
const app = read('src/App.vue')
const editor = read('src/components/panels/FileEditorPane.vue')
const tree = read('src/components/panels/FileTreePanel.vue')

// ---- 侧栏视图状态在 ui store，外部入口可切 ----
expect(
  /const sidebarView = ref<SidebarView>\('chats'\)/.test(ui),
  'ui.ts 未持有 sidebarView 状态（编辑器无法切到文件树）',
)
expect(
  /function requestFileTree\(\)/.test(ui) && /sidebarView\.value = 'files'/.test(ui),
  'ui.ts 缺少 requestFileTree',
)
expect(
  /requestFileTree[\s\S]{0,200}sidebarOpenRequest\.value \+= 1/.test(ui),
  'requestFileTree 未请求展开侧栏（侧栏收起时点了看不见）',
)
expect(
  /function requestFileTree\(\) \{\s*\n\s*if \(!agentsStore\.currentAgent\?\.project_mode\) return/.test(ui),
  'requestFileTree 未按项目模式门控（非项目模式会被守卫立刻弹回）',
)

// ---- 侧栏读取 store 状态，不再自己持有 ----
expect(
  /const \{ sidebarView \} = storeToRefs\(uiStore\)/.test(sidebar),
  'LeftSidebar.vue 未改用 ui store 的 sidebarView',
)
expect(
  !/const sidebarView = ref<'chats' \| 'files'>/.test(sidebar),
  'LeftSidebar.vue 仍持有局部的 sidebarView',
)
expect(
  /uiStore\.setSidebarView\('files'\)/.test(sidebar),
  'LeftSidebar.vue 的「文件」按钮未走 store',
)

// ---- App 消费展开请求 ----
expect(
  /watch\(\(\) => uiStore\.sidebarOpenRequest[\s\S]{0,220}sidebarCollapsed\.value = false/.test(app),
  'App.vue 未消费 sidebarOpenRequest（侧栏收起时不会展开）',
)

// ---- 编辑器两个入口都切视图 ----
expect(
  /function revealInTree\(seg: BreadcrumbSeg\) \{[\s\S]{0,160}uiStore\.requestFileTree\(\)/.test(editor),
  '面包屑点击未切到文件树视图',
)
expect(
  /function revealActiveInTree\(\)[\s\S]{0,260}uiStore\.requestFileTree\(\)/.test(editor),
  '「定位」按钮未切到文件树视图',
)
expect(
  !/watch\(\(\) => store\.activePath[\s\S]{0,300}requestFileTree/.test(editor),
  '切换文件标签的自动跟随不应把用户拽到文件树视图',
)

// ---- 挂载时补消费未处理的定位请求 ----
expect(
  /async function handleReveal\(path: string\)/.test(tree),
  'FileTreePanel.vue 未抽出 handleReveal',
)
expect(
  /watch\(\(\) => store\.revealPath, handleReveal\)/.test(tree),
  'FileTreePanel.vue 未监听 revealPath',
)
expect(
  /onMounted\(\(\) => \{[\s\S]*?if \(store\.revealPath\) void handleReveal\(store\.revealPath\)/.test(tree),
  'FileTreePanel.vue 未在挂载时补消费定位请求（侧栏从会话列表切过来会丢定位）',
)

if (failures.length > 0) {
  console.error('文件树定位契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('文件树定位契约测试通过')
