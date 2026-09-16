import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = (p) => readFileSync(join(root, p), 'utf8')
const exists = (p) => existsSync(join(root, p))

const rightPanel = read('src/components/layout/RightPanel.vue')
const uiStore = read('src/stores/ui.ts')
const app = read('src/App.vue')
const badge = read('src/components/chat/FileChangesBadge.vue')
const roundCard = read('src/components/chat/RoundFileChangesCard.vue')
const fileCard = read('src/components/chat/tools/ToolFileCard.vue')
const fileChangesPanel = read('src/components/panels/FileChangesPanel.vue')

const failures = []

function expect(cond, message) {
  if (!cond) failures.push(message)
}

function expectMatch(content, pattern, message) {
  if (!pattern.test(content)) failures.push(message)
}

// 1. tab 按钮存在且顺序为 模型/能力/变更/(文件)/任务
// 只按 tabs 列表的定义（id: 'xxx'）比顺序：文件别处也会出现这些裸字符串
// （例如滚动容器的 :class="{ 'is-editor': activeTab === 'editor' }"），按裸字符串比对会误判
const tabOrder = ['model', 'abilities', 'changes', 'editor', 'tasks']
let cursor = -1
for (const id of tabOrder) {
  const at = rightPanel.indexOf(`id: '${id}'`)
  expect(at >= 0, `RightPanel.vue 缺少 tab ${id}`)
  expect(at > cursor, `RightPanel.vue tab 顺序错误：${id} 位置不对`)
  cursor = at
}
expect(!rightPanel.includes("'appearance'"), 'RightPanel.vue 仍残留 appearance tab（外观已并入模型）')
expect(rightPanel.includes('v-for="tab in tabs"'), 'RightPanel.vue 未按 tabs 列表渲染 tab 按钮')
expect(
  uiStore.includes("export type RightPanelTab = 'model' | 'abilities' | 'changes' | 'editor' | 'tasks'"),
  'ui store 缺少 RightPanelTab 联合类型',
)
expect(
  uiStore.includes("export const RIGHT_PANEL_TABS: RightPanelTab[] = ['model', 'abilities', 'changes', 'editor', 'tasks']"),
  'ui store 缺少 RIGHT_PANEL_TABS 顺序定义',
)
// 文件查看区：打开的文件以标签展示，editor tab 渲染 FileEditorPane
expect(
  /list\.push\(\{ id: 'editor'/.test(rightPanel),
  'RightPanel.vue 缺少 editor tab',
)
expect(rightPanel.includes('<FileEditorPane'), 'RightPanel.vue editor tab 未渲染 FileEditorPane')
expect(rightPanel.includes('import FileEditorPane'), 'RightPanel.vue 未导入 FileEditorPane')

// 文件树：懒加载 + 递归节点 + 项目目录沙箱
const treeNode = read('src/components/panels/FileTreeNode.vue')
const treeStore = read('src/stores/project-tree.ts')
const api = read('src/api/http.ts')
expect(treeNode.includes("defineOptions({ name: 'FileTreeNode' })"), 'FileTreeNode.vue 缺少递归所需的组件名')
expect(treeNode.includes('<FileTreeNode'), 'FileTreeNode.vue 未递归渲染子节点')
expect(
  /if \(store\.isLoaded\(props\.entry\.path\)\) return/.test(treeNode),
  'FileTreeNode.vue 展开目录时未做已加载短路（非懒加载）',
)
expect(
  treeStore.includes('const children = ref<Record<string, ProjectTreeEntry[]>>({})'),
  'project-tree store 未按目录路径缓存子层内容',
)
expect(
  api.includes('/tools/project/tree?agent_id='),
  'http.ts 缺少项目文件树接口',
)

// git 分支：项目名旁显示当前分支，非 git 仓库时后端返回 null
expect(
  api.includes('git_branch?: string | null'),
  'http.ts 未声明 git_branch 字段',
)
expect(
  treeStore.includes('gitBranch'),
  'project-tree store 未保存 git 分支',
)

// 全项目搜索：不再用「只过滤已展开层」的本地过滤
const treePanel = read('src/components/panels/FileTreePanel.vue')
expect(
  /store\.gitBranch/.test(treePanel),
  'FileTreePanel.vue 未展示 git 分支',
)
expect(
  api.includes('/tools/project/search?agent_id='),
  'http.ts 缺少全项目搜索接口',
)
expect(
  /api\.searchProjectFiles\(/.test(treePanel),
  'FileTreePanel.vue 搜索框未走后端全项目搜索',
)
expect(
  !/过滤当前层/.test(treePanel),
  'FileTreePanel.vue 仍保留「过滤当前层」的误导文案',
)
expect(
  !treePanel.includes(':filter="filter"'),
  'FileTreePanel.vue 仍在向下传本地 filter（应改为全项目搜索）',
)
expect(
  !treeNode.includes('visibleChildren'),
  'FileTreeNode.vue 仍在本地过滤子项（应改为全项目搜索）',
)
expect(
  !/props\.filter/.test(treeNode),
  'FileTreeNode.vue 仍依赖 filter prop',
)

// 2. 默认 tab 为模型
expectMatch(
  uiStore,
  /function loadActiveTab\(\)[\s\S]*return 'model'/,
  'ui store 默认 tab 必须回落到 model',
)
// 任务进度只属于任务 tab：不得放在跨 tab 置顶区，也不得残留置顶样式
expect(!rightPanel.includes('right-panel-pinned'), 'RightPanel.vue 仍残留跨 tab 的待办置顶区（任务进度只能在任务 tab 内）')
expect(
  /<template v-if="activeTab === 'tasks'">[\s\S]*<TodoList :todos="chatStore\.todos"/.test(rightPanel),
  '任务进度未收进任务 tab 内部',
)
expect(rightPanel.includes('<TodoList'), 'RightPanel.vue 未渲染任务进度 TodoList')
expect(rightPanel.includes("import TodoList from '@/components/panels/TodoList.vue'"), 'RightPanel.vue 未导入 TodoList')
expect(
  /const activeTab = ref<RightPanelTab>\(loadActiveTab\(\)\)/.test(uiStore),
  'ui store 初始化未读取记忆的 tab',
)

// 3. last-tab localStorage 记忆逻辑存在
expect(uiStore.includes("'lc-agent:right-panel:activeTab'"), 'ui store 缺少 last-tab localStorage key')
expect(
  /watch\(activeTab, \(tab\) => \{[\s\S]*localStorage\.setItem\(ACTIVE_TAB_KEY, tab\)/.test(uiStore),
  'ui store 未在 tab 变化时写入 localStorage',
)
expect(
  /localStorage\.getItem\(ACTIVE_TAB_KEY\)/.test(uiStore),
  'ui store 未在初始化时读取 localStorage',
)

// 4. 切换 agent 重置回模型
expectMatch(
  uiStore,
  /watch\(\(\) => agentsStore\.currentAgentId, \(\) => \{\s*activeTab\.value = 'model'\s*\}\)/,
  'ui store 未在切换 agent 时把 tab 重置回模型',
)

// 5. badge 规则：运行中进程数 / MCP error 数，> 0 才显示
expect(
  /const runningProcessCount = computed\(\(\) =>[\s\S]*status\.startsWith\('running'\)/.test(rightPanel),
  'RightPanel.vue 缺少运行中后台进程计数',
)
expect(
  /const mcpErrorCount = computed\(\(\) =>[\s\S]*server\.status === 'error'/.test(rightPanel),
  'RightPanel.vue 缺少 MCP 错误计数',
)
expect(rightPanel.includes('v-if="tab.badge > 0"'), 'RightPanel.vue badge 未按「有异常才亮」显示')
expect(
  /id: 'abilities'[\s\S]*badge: mcpErrorCount\.value/.test(rightPanel),
  '能力 tab 未接 MCP 错误 badge',
)
expect(
  /id: 'tasks'[\s\S]*badge: runningProcessCount\.value/.test(rightPanel),
  '任务 tab 未接后台进程 badge',
)

// 6. 旧 section 全有归属，一个不能丢（外观三项已并入模型 tab）
const modelTabOwned = ['模型', '思考级别', '温度', '窗口裁剪模型', '会话', 'Thread', 'Markdown 版式', 'Markdown 色盘', '输入框动画']
const abilitiesTabOwned = ['工具', 'MCP 服务器', 'Skills', 'PermissionsPanel']
const tasksTabOwned = ['自动化任务', 'Agent 启动的后台进程', 'formatElapsed']
for (const text of [...modelTabOwned, ...abilitiesTabOwned, ...tasksTabOwned]) {
  expect(rightPanel.includes(text), `RightPanel.vue 丢失原 section 内容：${text}`)
}

// 7. FileChangesDrawer overlay 不再被挂载；Badge 跳 tab 逻辑存在
expect(!exists('src/components/chat/FileChangesDrawer.vue'), '旧 FileChangesDrawer.vue 未删除')
expect(!app.includes('FileChangesDrawer'), 'App.vue 仍在挂载 FileChangesDrawer')
expect(app.includes('<FileChangesPanel') || rightPanel.includes('<FileChangesPanel'), '变更 tab 未接入 FileChangesPanel')
expect(rightPanel.includes('<FileChangesPanel />'), 'RightPanel.vue 变更 tab 未渲染 FileChangesPanel')
expect(badge.includes("uiStore.requestTab('changes')"), 'FileChangesBadge.vue 点击未改为切到变更 tab')
expect(roundCard.includes("uiStore.requestTab('changes'"), 'RoundFileChangesCard.vue 未改为切到变更 tab')
expect(fileCard.includes("uiStore.requestTab('changes'"), 'ToolFileCard.vue 未改为切到变更 tab')
expect(
  /function requestTab\(tab: RightPanelTab, target\?: \{ round\?: number \| null; filePath\?: string \}\)/.test(uiStore),
  'ui store requestTab 未支持携带轮次/文件定位参数',
)
expect(uiStore.includes('rightPanelOpenRequest'), 'ui store 缺少右侧面板展开请求信号')
expect(
  /watch\(\(\) => uiStore\.rightPanelOpenRequest[\s\S]*rightCollapsed\.value = false/.test(app),
  'App.vue 未在收起状态下响应展开请求',
)

// 8. tab 栏 flex-wrap 换行样式存在
expectMatch(
  rightPanel,
  /\.right-panel-tabs\s*\{[\s\S]*flex-wrap:\s*wrap/,
  'tab 栏缺少 flex-wrap 折行样式',
)
expectMatch(
  rightPanel,
  /\.panel-tab\s*\{[\s\S]*white-space:\s*nowrap/,
  'tab 按钮缺少 nowrap，窄栏会断字',
)
expectMatch(
  rightPanel,
  /\.panel-tab\.active\s*\{[\s\S]*linear-gradient\(135deg/,
  'tab 激活态缺少渐变胶囊样式',
)
expect(rightPanel.includes('prefers-reduced-motion'), 'RightPanel.vue 缺少 reduced-motion 兜底')

// 变更 tab 内容：双源 + 轮次 + diff 模式，且不再依赖抽屉
expect(fileChangesPanel.includes("changeSource === 'agent'"), 'FileChangesPanel.vue 缺少 Agent 修改源')
expect(fileChangesPanel.includes("changeSource === 'git'"), 'FileChangesPanel.vue 缺少 Git Diff 源')
expect(fileChangesPanel.includes('selectedRound'), 'FileChangesPanel.vue 缺少轮次筛选')
expect(fileChangesPanel.includes("'side-by-side'"), 'FileChangesPanel.vue 缺少 side-by-side diff 模式')
expect(!fileChangesPanel.includes('el-drawer'), 'FileChangesPanel.vue 仍残留 el-drawer 外壳')
expect(
  /watch\(\(\) => uiStore\.activeTab[\s\S]*switchToSession/.test(fileChangesPanel),
  'FileChangesPanel.vue 未在切到变更 tab 时拉取数据',
)

// 文件预览弹层：行号栏 + 选中右键自定义菜单（复制 / 复制行号 / 复制行号和内容）
const codeModal = read('src/components/chat/CodeBlockModal.vue')
expect(
  /sourcePath\?: string/.test(codeModal),
  'CodeBlockModal.vue 缺少 sourcePath 属性',
)
expect(codeModal.includes('code-gutter'), 'CodeBlockModal.vue 缺少行号栏')
expect(codeModal.includes('@contextmenu="handleContextMenu"'), 'CodeBlockModal.vue 未接管右键菜单')
expect(codeModal.includes('复制行号'), 'CodeBlockModal.vue 缺少「复制行号」菜单项')
expect(codeModal.includes('复制行号和内容'), 'CodeBlockModal.vue 缺少「复制行号和内容」菜单项')
expect(
  /function selectionLineRange\(\)/.test(codeModal),
  'CodeBlockModal.vue 缺少从选区反推行号的逻辑',
)
expect(
  /`\$\{props\.sourcePath\}#\$\{span\}`/.test(codeModal),
  'CodeBlockModal.vue 行号复制格式不是「路径#Lx-y」',
)
// 文件树不再走预览弹层：点击文件统一打开 editor 标签
expect(
  !treePanel.includes('CodeBlockModal'),
  'FileTreePanel.vue 仍残留预览弹层（应改为标签打开）',
)
expect(
  /openedFilesStore\.open\(/.test(treePanel),
  'FileTreePanel.vue 未通过 opened-files store 打开文件标签',
)
// 左侧栏：Chats / 文件 视图切换，文件树嵌入侧栏
const leftSidebar = read('src/components/layout/LeftSidebar.vue')
expect(leftSidebar.includes('sidebarView'), 'LeftSidebar.vue 缺少视图切换状态')
expect(leftSidebar.includes('<FileTreePanel'), 'LeftSidebar.vue 未嵌入 FileTreePanel')
// opened-files store：标签列表 + 激活 + 内容缓存
const openedFiles = read('src/stores/opened-files.ts')
expect(/function open\(path: string/.test(openedFiles), 'opened-files store 缺少 open()')
expect(/function close\(path: string/.test(openedFiles), 'opened-files store 缺少 close()')
expect(openedFiles.includes("requestTab('editor')"), 'opened-files store 打开文件未切到 editor tab')
// FileEditorPane：标签栏 + 关闭 + 内容查看
const editorPane = read('src/components/panels/FileEditorPane.vue')
expect(editorPane.includes('editor-tab'), 'FileEditorPane.vue 缺少文件标签栏')
expect(editorPane.includes('store.close('), 'FileEditorPane.vue 标签缺少关闭按钮')

// 后端 tree 端点必须真的返回 git_branch（前端拿到字段≠后端吐了字段）
const backendTools = readFileSync(join(root, '..', 'lc_agent/server/routes/tools.py'), 'utf8')
expect(
  /"git_branch": await asyncio\.to_thread\(_git_branch_info, project_root\)/.test(backendTools),
  "后端 tools.py 的 /tools/project/tree 未返回 git_branch",
)
expect(
  /def _git_branch_info\(project_root: Path\) -> str \| None:/.test(backendTools),
  '后端 tools.py 缺少 _git_branch_info',
)

// 文件类型徽标：按后缀给出不同标签与配色，文件树与搜索共用同一组件
const fileTypeUtil = read('src/utils/file-type.ts')
const fileTypeIcon = read('src/components/common/FileTypeIcon.vue')
expect(exists('src/components/common/FileTypeIcon.vue'), '缺少共用的 FileTypeIcon 组件')
expect(
  /export function fileTypeMeta\(name: string\)/.test(fileTypeUtil),
  'file-type.ts 未导出 fileTypeMeta',
)
for (const [ext, label] of [['py', "'PY'"], ['md', "'MD'"], ['java', "'JAVA'"], ['json', "'JSON'"]]) {
  expect(
    new RegExp(`${ext}: \\{ label: ${label.replace(/[']/g, "'")}`).test(fileTypeUtil),
    `file-type.ts 缺少 .${ext} 的类型映射`,
  )
}
expect(treePanel.includes('<FileTypeIcon'), 'FileTreePanel.vue 搜索结果未使用 FileTypeIcon')
expect(treeNode.includes('<FileTypeIcon'), 'FileTreeNode.vue 未使用 FileTypeIcon')
// 旧的「统一 Document 图标」方案应已移除
expect(!treeNode.includes('EXT_ICON'), 'FileTreeNode.vue 仍残留旧的 EXT_ICON 映射')
expect(!treeNode.includes('EXT_COLOR'), 'FileTreeNode.vue 仍残留旧的 EXT_COLOR 映射')
expect(!treePanel.includes('result-icon'), 'FileTreePanel.vue 仍残留旧的 result-icon 样式')

// Git Diff 按钮：按「项目是否为 git 仓库」显示，而非「本会话是否改过文件」
const panel = read('src/components/panels/FileChangesPanel.vue')
const changesStore = read('src/stores/file-changes.ts')
const backendChanges = readFileSync(join(root, '..', 'lc_agent/server/routes/file_changes.py'), 'utf8')
expect(
  /v-if="store\.gitAvailable"/.test(panel),
  'FileChangesPanel.vue 的 Git Diff 按钮未改为按 store.gitAvailable 显示',
)
expect(
  !/v-if="store\.gitBaseHash"/.test(panel),
  'FileChangesPanel.vue 仍残留旧的 gitBaseHash 门控',
)
expect(
  /const gitAvailable = computed\(\(\) => _active\.value\?\.gitAvailable \?\? false\)/.test(changesStore),
  'file-changes.ts 缺少 gitAvailable 状态',
)
expect(
  /gitBaseline\.value = store\.gitBaseHash \? 'session' : 'head'/.test(panel),
  'FileChangesPanel.vue 缺少「无会话基准时回退 HEAD」逻辑',
)
expect(
  /"git_available": git_available/.test(backendChanges),
  '后端 file-changes 列表接口未返回 git_available',
)
expect(
  /def _resolve_project_dir\(sess, engine\)/.test(backendChanges),
  '后端缺少 _resolve_project_dir（由 agent 项目目录解析 git 仓库）',
)
expect(
  /async def _get_git_context\(session_id: str, user: User, db: AsyncSession, engine=None\)/.test(backendChanges),
  '后端 _get_git_context 未接收 engine 参数',
)

if (failures.length > 0) {
  console.error('右侧面板 Tab 契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('右侧面板 Tab 契约测试通过')
