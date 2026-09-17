import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = (p) => readFileSync(join(root, p), 'utf8')
const exists = (p) => existsSync(join(root, p))

const failures = []

function expect(cond, message) {
  if (!cond) failures.push(message)
}

// ---- 文件存在性 ----
expect(exists('src/stores/session-tabs.ts'), '缺少 src/stores/session-tabs.ts')
expect(exists('src/components/layout/SessionTabs.vue'), '缺少 src/components/layout/SessionTabs.vue')
expect(exists('src/stores/chat-ui-state.ts'), '缺少 src/stores/chat-ui-state.ts')

const tabsStore = read('src/stores/session-tabs.ts')
const tabsBar = read('src/components/layout/SessionTabs.vue')
const app = read('src/App.vue')
const chatStore = read('src/stores/chat.ts')
const sessionsStore = read('src/stores/sessions.ts')
const chatView = read('src/views/ChatView.vue')
const chatInput = read('src/components/chat/ChatInput.vue')
const fileChanges = read('src/stores/file-changes.ts')
const tabMenu = read('src/components/common/TabListMenu.vue')
const agentIconUtil = read('src/utils/agentIcon.ts')

// ---- R2-Q5 刷新后恢复：标签集合与激活项持久化 ----
expect(
  /OPEN_TABS_KEY[\s\S]*localStorage\.getItem/.test(tabsStore),
  'session-tabs.ts 未持久化标签集合到 localStorage',
)
expect(
  /ACTIVE_TAB_KEY[\s\S]*localStorage\.setItem/.test(tabsStore),
  'session-tabs.ts 未持久化激活标签',
)
expect(
  /function restoreTabs\(/.test(tabsStore),
  'session-tabs.ts 缺少 restoreTabs（恢复时过滤已删除会话）',
)

// ---- R2-Q2 去重：点击已打开会话不再开重复标签 ----
expect(
  /function openTab\(id: string\)[\s\S]{0,200}includes\(id\)/.test(tabsStore),
  'session-tabs.ts 的 openTab 未做去重',
)

// ---- R2-Q6 关闭后激活右邻 ----
expect(
  /Math\.min\(idx, remaining\.length - 1\)/.test(tabsStore),
  'session-tabs.ts 关闭标签后未按「右邻优先」选择下一个激活项',
)

// ---- R3-Q2 导航栈按标签隔离 ----
expect(
  /navStacks[\s\S]*Record<string, NavStackEntry\[\]>|navStacks\.value/.test(tabsStore),
  'session-tabs.ts 缺少按标签隔离的导航栈',
)
expect(
  /sessionNavStack = computed/.test(sessionsStore),
  'sessions.ts 的导航栈未改为按标签读取的 computed',
)
expect(
  !/sessionNavStack\.value\.push\(/.test(sessionsStore),
  'sessions.ts 仍在直接 push 全局导航栈',
)
expect(
  !/sessionNavStack\.value = \[\]/.test(sessionsStore),
  'sessions.ts 仍在直接重置全局导航栈',
)

// ---- R1-Q2 点击侧边栏会话 = 开标签 ----
expect(
  /async function handleSwitchSession\(sessionId: string\)[\s\S]{0,200}openTab\(sessionId\)/.test(app),
  'App.vue 的 handleSwitchSession 未打开标签',
)

// ---- 保活：只有不在标签里的会话才回收 ----
expect(
  /function _releaseAfterStreamEnd\(/.test(chatStore),
  'chat.ts 缺少 _releaseAfterStreamEnd',
)
expect(
  /isTabOpen\(sessionId\)[\s\S]{0,80}return/.test(chatStore),
  'chat.ts 的回收逻辑未受「是否为已打开标签」约束',
)
expect(
  /if \(old && !old\.isStreaming\.value && !useSessionTabsStore\(\)\.isTabOpen\(oldId\)\) \{/.test(chatStore),
  'chat.ts 的 switchToSession 未按「空闲 + 非标签」才回收离开的会话',
)
expect(
  !/if \(old && !old\.isStreaming\.value\) \{/.test(chatStore),
  'chat.ts 的 switchToSession 仍保留旧的「空闲即回收」判断',
)
expect(
  /function releaseSession\(sessionId: string\)/.test(chatStore),
  'chat.ts 缺少 releaseSession（关闭标签时释放缓存）',
)

// ---- R3-Q3 关闭标签即断开 ----
expect(
  /closeTab\(sessionId\)[\s\S]{0,200}releaseSession\(sessionId\)/.test(app),
  'App.vue 的 handleTabClose 未释放会话缓存',
)

// ---- R2-Q1 不设上限：不存在自动淘汰逻辑 ----
expect(
  !/MAX_TABS|MAX_OPEN_TABS|evict/i.test(tabsStore),
  'session-tabs.ts 出现了标签上限/淘汰逻辑（决策为不设上限）',
)

// ---- id 改写时原子搬迁标签 ----
expect(
  /persistSession[\s\S]{0,900}renameTab\(id, newId\)/.test(sessionsStore),
  'sessions.ts 的 persistSession 未搬迁标签 key（会留下幽灵标签）',
)
expect(
  /function renameTab\(oldId: string, newId: string\)/.test(tabsStore),
  'session-tabs.ts 缺少 renameTab',
)

// ---- 会话删除时移除标签 ----
expect(
  /deleteSession[\s\S]{0,600}removeTab\(id\)/.test(sessionsStore),
  'sessions.ts 的 deleteSession 未移除对应标签',
)

// ---- R3-Q5 横向滚动 + 激活项自动滚入可视区 ----
expect(
  /overflow-x: auto/.test(tabsBar),
  'SessionTabs.vue 未开启横向滚动',
)
expect(
  /scrollLeft/.test(tabsBar),
  'SessionTabs.vue 未实现激活标签自动滚入可视区',
)

// ---- 标签状态点：流式中 / 已完成未查看 ----
expect(
  /isSessionStreaming\(id\)/.test(tabsBar),
  'SessionTabs.vue 未显示流式状态点',
)
expect(
  /isCompletedUnseen\(id\)/.test(tabsBar),
  'SessionTabs.vue 未显示「已完成未查看」标记',
)

// ---- 下拉列表显示所属 Agent 名 ----
expect(
  /getAgentName\(session\.agent_id\)/.test(tabsBar),
  'SessionTabs.vue 的下拉列表未显示会话所属 Agent 名',
)
expect(
  /<template #extra="{ item }">[\s\S]*?session-tab-agent/.test(tabsBar),
  'SessionTabs.vue 未把 Agent 名放进下拉列表的 extra 插槽',
)
expect(
  /:width="320"/.test(tabsBar),
  'SessionTabs.vue 未放宽下拉面板宽度（标题 + Agent 名放不下）',
)
expect(
  /getAgentIcon\(agent\)/.test(tabsBar) && /agentIcon: getAgentIcon/.test(tabsBar),
  'SessionTabs.vue 未给 Agent 名配图标',
)
expect(
  /export function getAgentIcon/.test(agentIconUtil),
  '缺少 utils/agentIcon.ts（图标逻辑应三处共用）',
)
expect(
  !/function getAgentIcon/.test(read('src/components/layout/AppHeader.vue')),
  'AppHeader.vue 仍保留局部的 getAgentIcon（应改用 utils/agentIcon.ts）',
)
expect(
  !/function getAgentIcon/.test(read('src/components/layout/LeftSidebar.vue')),
  'LeftSidebar.vue 仍保留局部的 getAgentIcon（应改用 utils/agentIcon.ts）',
)

// ---- 下拉面板加高（会话 / 文件共用同一个组件） ----
expect(
  /max-height: min\(620px, 76vh\)/.test(tabMenu),
  'TabListMenu.vue 的下拉面板未加高',
)

// ---- 每会话滚动位置 ----
expect(
  /rememberScrollTop/.test(chatView),
  'ChatView.vue 未记录每会话滚动位置',
)
expect(
  /restoreScrollPosition/.test(chatView),
  'ChatView.vue 未恢复每会话滚动位置',
)
expect(
  /if \(oldId && !messages\.value\.some\(m => m\.id === oldId\)\) return/.test(chatView),
  'ChatView.vue 未抑制「切换会话时无条件滚到底」',
)

// ---- 每标签草稿 ----
expect(
  /rememberDraft/.test(chatInput),
  'ChatInput.vue 未按会话保存草稿',
)
expect(
  /getDraft\(sessionId\)/.test(chatInput),
  'ChatInput.vue 未按会话恢复草稿',
)

// ---- R3-Q4 文件变更按会话分桶 ----
expect(
  /bySession = reactive\(new Map<string, SessionChangesState>\(\)\)/.test(fileChanges),
  'file-changes.ts 未改为按 sessionId 分桶',
)
expect(
  /function switchToSession\(sessionId: string\)[\s\S]{0,200}state\?\.loaded/.test(fileChanges),
  'file-changes.ts 的 switchToSession 未命中缓存则跳过重拉',
)
expect(
  /function dropSession\(/.test(fileChanges),
  'file-changes.ts 缺少 dropSession（关闭标签时丢弃缓存）',
)

// ---- 标签栏位置：贴在中间聊天列顶部 ----
expect(
  /<main class="chat-main">[\s\S]{0,200}<SessionTabs/.test(app),
  'SessionTabs 未放在中间聊天列顶部',
)

// ---- R2-Q3 只管聊天会话：Admin / Usage 不显示标签栏 ----
expect(
  /v-if="isChatRoute"/.test(app),
  'SessionTabs 未按「聊天路由」门控（会在 Admin/Usage 页也显示）',
)
expect(
  !/v-if="!isPublicRoute"\s*\n\s*@activate="handleTabActivate"/.test(app),
  'SessionTabs 仍按 isPublicRoute 门控',
)

if (failures.length > 0) {
  console.error('会话标签栏契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('会话标签栏契约测试通过')
