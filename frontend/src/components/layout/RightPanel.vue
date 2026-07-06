<template>
  <aside class="right-panel">
    <div class="right-panel-fixed">
      <template v-if="!agentsStore.isCodeAgent">
        <div class="panel-section">
          <h4>模型</h4>
          <ModelSelector
            :models="toolsStore.models"
            :current-model="toolsStore.currentModel"
            @change="toolsStore.setModel"
          />
          <div class="llm-params-controls">
            <div class="param-row">
              <div class="param-label-group">
                <span class="param-label">思考级别</span>
                <span v-if="reasoningFromPreset" class="param-source-hint">预设</span>
                <span v-else-if="hasReasoningOverride" class="param-source-hint override">覆盖</span>
              </div>
              <div class="param-control-group">
                <el-select
                  :model-value="effectiveReasoningEffort ?? 'default'"
                  size="small"
                  class="reasoning-effort-select"
                  @update:model-value="(v: string) => toolsStore.setLlmParam('reasoning_effort', v === 'default' ? null : v)"
                >
                  <el-option
                    v-for="effort in ['default', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh']"
                    :key="effort"
                    :label="effort"
                    :value="effort"
                  />
                </el-select>
                <button
                  v-if="hasReasoningOverride"
                  class="param-reset-btn"
                  type="button"
                  title="清除覆盖，恢复预设/默认"
                  @click="toolsStore.setLlmParam('reasoning_effort', null)"
                >×</button>
              </div>
            </div>
            <div class="param-row param-row-slider">
              <div class="param-label-group">
                <span class="param-label">温度</span>
                <span v-if="temperatureFromPreset" class="param-source-hint">预设</span>
                <span v-else-if="hasTemperatureOverride" class="param-source-hint override">覆盖</span>
              </div>
              <div class="temperature-control">
                <el-slider
                  :model-value="effectiveTemperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  size="small"
                  class="temperature-slider"
                  @update:model-value="(v: number) => toolsStore.setLlmParam('temperature', v)"
                />
                <el-input-number
                  :model-value="effectiveTemperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  :precision="1"
                  size="small"
                  controls-position="right"
                  class="temperature-input"
                  @update:model-value="(v: number | undefined) => toolsStore.setLlmParam('temperature', v ?? null)"
                />
                <button
                  v-if="hasTemperatureOverride"
                  class="param-reset-btn"
                  type="button"
                  title="清除覆盖，恢复预设/默认"
                  @click="toolsStore.setLlmParam('temperature', null)"
                >×</button>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section window-trim-section">
          <div class="window-trim-control">
            <h4>窗口裁剪模型</h4>
            <el-switch
              :model-value="summEnabled"
              size="small"
              @change="(val: boolean) => { summEnabled = val; updateSummarization({ enabled: val }) }"
            />
          </div>
          <el-select
            v-if="summEnabled"
            v-model="summModel"
            placeholder="默认同主模型"
            size="small"
            filterable
            clearable
            class="window-trim-select"
            @change="updateSummarization({ default_model: $event || '' })"
          >
            <el-option
              v-for="model in toolsStore.models"
              :key="model.id"
              :label="model.id"
              :value="model.id"
            />
          </el-select>
        </div>
      </template>

      <div class="panel-section markdown-theme-section">
        <div class="section-header compact-section-header">
          <h4>Markdown 风格</h4>
          <span class="theme-current">{{ currentOption.label }}</span>
        </div>
        <el-select
          v-model="markdownTheme"
          size="small"
          class="markdown-theme-select"
          @change="(value: MarkdownThemeId) => setMarkdownTheme(value)"
        >
          <el-option
            v-for="option in MARKDOWN_THEME_OPTIONS"
            :key="option.id"
            :label="option.label"
            :value="option.id"
          >
            <div class="theme-option-row">
              <span class="theme-option-dot" :style="{ background: option.accent }"></span>
              <div class="theme-option-copy">
                <span class="theme-option-name">{{ option.label }}</span>
                <span class="theme-option-desc">{{ option.description }}</span>
              </div>
            </div>
          </el-option>
        </el-select>
      </div>

      <div v-if="chatStore.todos.length > 0" class="panel-section">
        <TodoList :todos="chatStore.todos" />
      </div>
    </div>

    <div class="right-panel-scroll">
      <div v-if="agentsStore.isCodeAgent" class="panel-section code-agent-hint">
        <div class="hint-box code-agent-box">
          <span class="hint-icon">⚙️</span>
          <span class="hint-text">代码智能体</span>
          <span class="hint-sub">此智能体由代码注册，工具、MCP、Skills、提示词和模型由代码中的 graph 决定。当前面板的框架级配置不适用于它。</span>
        </div>
      </div>

      <template v-if="!agentsStore.isChatAgent && !agentsStore.isCodeAgent">
        <div class="panel-section">
          <h4>工具</h4>
          <ToolGroupPanel
            :groups="toolsStore.filteredGroups"
            @toggle="toolsStore.toggleGroup"
            @detail="(group) => openDetail('tool-group', group.description || group.id, group)"
          />
        </div>

        <div class="panel-section">
          <div class="section-header">
            <h4>MCP 服务器</h4>
            <button class="refresh-btn" type="button" :disabled="toolsStore.mcpRefreshing" @click="toolsStore.refreshMcpServers()">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                :class="{ spinning: toolsStore.mcpRefreshing }"
              >
                <path d="M21 2v6h-6" />
                <path d="M3 12a9 9 0 0 1 15.55-6.36L21 8" />
                <path d="M3 22v-6h6" />
                <path d="M21 12a9 9 0 0 1-15.55 6.36L3 16" />
              </svg>
              刷新
            </button>
          </div>
          <div v-for="server in toolsStore.filteredMcp" :key="server.name" class="mcp-item" :class="{ 'not-allowed': !server.allowed }">
            <div class="mcp-header">
              <div class="mcp-left">
                <el-switch
                  :model-value="server.enabled"
                  :disabled="!server.allowed"
                  size="small"
                  @change="toolsStore.toggleMcp(server.name)"
                />
                <span class="mcp-name">{{ server.name }}</span>
                <button class="detail-btn" type="button" @click="openDetail('mcp', server.name, server)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  详情
                </button>
              </div>
              <el-tag size="small" :type="!server.allowed ? 'warning' : server.status === 'connected' ? 'success' : server.status === 'error' ? 'danger' : server.status === 'disabled' ? 'warning' : 'info'">
                {{ !server.allowed ? '未授权' : server.status === 'connected' ? '已连接' : server.status === 'error' ? '错误' : server.status === 'disabled' ? '已禁用' : '未连接' }}
              </el-tag>
            </div>
            <div v-if="server.error && server.allowed" class="mcp-error">{{ server.error }}</div>
            <div v-if="server.tools && server.tools.length && server.allowed" class="mcp-tools">
              <el-tag v-for="tool in server.tools.slice(0, 5)" :key="tool" size="small" :class="server.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'">{{ tool }}</el-tag>
              <el-tag v-if="server.tools.length > 5" size="small" :class="server.enabled ? 'tool-tag-enabled' : 'tool-tag-disabled'">+{{ server.tools.length - 5 }}</el-tag>
            </div>
          </div>
          <p v-if="!toolsStore.mcpServers.length" class="empty-hint">暂无 MCP 服务器</p>
        </div>

        <div class="panel-section">
          <h4>Skills</h4>
          <div v-for="skill in toolsStore.filteredSkills" :key="skill.name" class="skill-item" :class="{ 'not-allowed': !skill.allowed, 'skill-disabled': !skill.enabled }">
            <div class="skill-header">
              <el-switch
                :model-value="skill.enabled"
                :disabled="!skill.allowed"
                size="small"
                @change="toolsStore.toggleSkill(skill.name)"
              />
              <span class="skill-name" :class="{ dimmed: !skill.enabled }">{{ skill.name }}</span>
              <button class="detail-btn" type="button" @click="openDetail('skill', skill.name, skill)">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                详情
              </button>
            </div>
            <span class="skill-desc">{{ skill.description }}</span>
          </div>
          <p v-if="!toolsStore.skills.length" class="empty-hint">暂无 Skills</p>
        </div>

        <div class="panel-section">
          <PermissionsPanel />
        </div>
      </template>

      <div v-if="agentsStore.isChatAgent" class="panel-section chat-only-hint">
        <div class="hint-box">
          <span class="hint-icon">💬</span>
          <span class="hint-text">Chat 模式：纯对话，无工具</span>
          <span class="hint-sub">切换至 Empty 或 Power 智能体以启用工具</span>
        </div>
      </div>

      <div v-if="chatStore.threadId" class="panel-section status-section">
        <h4>会话</h4>
        <div class="status-item">
          <span>Thread:</span>
          <code>{{ chatStore.threadId.slice(0, 8) }}...</code>
        </div>
      </div>
    </div>

    <DetailModal
      v-model:visible="detailModal.visible"
      :title="detailModal.title"
      :mode="detailModal.mode"
      :data="detailModal.data"
    />
  </aside>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useToolsStore } from '@/stores/tools'
import { api } from '@/api/http'
import { useChatStore } from '@/stores/chat'
import { useAgentsStore } from '@/stores/agents'
import { useMarkdownTheme, MARKDOWN_THEME_OPTIONS, type MarkdownThemeId } from '@/composables/useMarkdownTheme'
import ModelSelector from '@/components/panels/ModelSelector.vue'
import ToolGroupPanel from '@/components/panels/ToolGroupPanel.vue'
import DetailModal from '@/components/panels/DetailModal.vue'
import TodoList from '@/components/panels/TodoList.vue'
import PermissionsPanel from '@/components/settings/PermissionsPanel.vue'

const toolsStore = useToolsStore()
const chatStore = useChatStore()
const agentsStore = useAgentsStore()

const presetLlmParams = computed(() => agentsStore.currentAgent?.llm_params ?? null)

const effectiveTemperature = computed(() =>
  toolsStore.llmParams?.temperature
    ?? presetLlmParams.value?.temperature
    ?? 0.7
)
const effectiveReasoningEffort = computed(() =>
  toolsStore.llmParams?.reasoning_effort
    ?? presetLlmParams.value?.reasoning_effort
    ?? null
)
const hasTemperatureOverride = computed(() => toolsStore.llmParams?.temperature !== undefined)
const hasReasoningOverride = computed(() => toolsStore.llmParams?.reasoning_effort !== undefined)
const temperatureFromPreset = computed(() =>
  !hasTemperatureOverride.value && presetLlmParams.value?.temperature !== undefined
)
const reasoningFromPreset = computed(() =>
  !hasReasoningOverride.value && presetLlmParams.value?.reasoning_effort !== undefined
)
const { markdownTheme, currentOption, setMarkdownTheme } = useMarkdownTheme()

const summEnabled = ref(true)
const summModel = ref('')

onMounted(async () => {
  try {
    const conf = await api.getSummarization()
    summEnabled.value = conf.enabled
    summModel.value = conf.default_model || ''
  } catch { /* ignore */ }
})

async function updateSummarization(data: { enabled?: boolean; default_model?: string }) {
  try {
    const res = await api.updateSummarization(data)
    summEnabled.value = res.enabled
    summModel.value = res.default_model || ''
  } catch { /* ignore */ }
}

const detailModal = reactive<{
  visible: boolean
  mode: 'tool-group' | 'mcp' | 'skill'
  title: string
  data: any
}>({
  visible: false,
  mode: 'tool-group',
  title: '',
  data: null,
})

async function openDetail(mode: 'tool-group' | 'mcp' | 'skill', title: string, data: any) {
  detailModal.mode = mode
  detailModal.title = title
  if (mode === 'skill' && data?.name && !data.body) {
    try {
      const detail = await api.getSkillDetail(data.name)
      detailModal.data = { ...data, ...detail }
    } catch {
      detailModal.data = data
    }
  } else {
    detailModal.data = data
  }
  detailModal.visible = true
}
</script>

<style scoped>
.right-panel {
  width: 350px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-panel-fixed {
  flex-shrink: 0;
  padding: 16px 16px 0;
}

.right-panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}

.panel-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
}

.markdown-theme-section {
  background: linear-gradient(180deg, color-mix(in srgb, var(--el-fill-color-light) 88%, var(--el-color-primary) 4%), var(--el-fill-color-light));
}

.window-trim-section,
.markdown-theme-section {
  margin-bottom: 14px;
}

.llm-params-controls {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.param-row-slider {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.param-label-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.param-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.param-source-hint {
  font-size: 10px;
  padding: 0 4px;
  border-radius: 3px;
  background: var(--el-fill-color);
  color: var(--el-text-color-placeholder);
  border: 1px solid var(--el-border-color-lighter);
  white-space: nowrap;
}

.param-source-hint.override {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.param-control-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.reasoning-effort-select {
  width: 100%;
}

.param-reset-btn {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 1px solid var(--el-border-color);
  border-radius: 50%;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.15s ease;
}

.param-reset-btn:hover {
  background: var(--el-color-danger-light-8);
  border-color: var(--el-color-danger-light-5);
  color: var(--el-color-danger);
}

.temperature-control {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.temperature-slider {
  flex: 1;
}

.temperature-input {
  width: 68px;
  flex-shrink: 0;
}

.window-trim-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.window-trim-select {
  width: 100%;
}

.compact-section-header {
  margin-bottom: 8px;
  padding-bottom: 0;
  border-bottom: none;
}

.theme-current {
  max-width: 132px;
  overflow: hidden;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markdown-theme-select {
  width: 100%;
}

.theme-option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.theme-option-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  box-shadow: 0 0 0 3px color-mix(in srgb, currentColor 12%, transparent);
  flex-shrink: 0;
}

.theme-option-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.theme-option-name {
  color: var(--el-text-color-primary);
  font-size: 12px;
  font-weight: 700;
}

.theme-option-desc {
  overflow: hidden;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-section h4 {
  margin: 0;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.7px;
  font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color);
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.18s ease;
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--el-color-primary-light-5);
  color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 6%, var(--el-bg-color));
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinning {
  animation: spin 0.9s linear infinite;
}

.empty-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 4px 0;
  opacity: 0.6;
}

.status-section .status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.status-section code {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.mcp-item {
  margin-bottom: 8px;
  padding: 8px 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease;
}

.mcp-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.mcp-item:has(.el-switch:not(.is-checked)) {
  opacity: 0.75;
  border: 1px dashed var(--el-color-warning-light-5) !important;
  background: var(--el-color-warning-light-9) !important;
}

.mcp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mcp-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mcp-error {
  font-size: 11px;
  color: var(--el-color-danger);
  margin-top: 4px;
  word-break: break-all;
  opacity: 0.8;
}

.mcp-name {
  font-size: 13px;
  font-weight: 500;
}

.mcp-tools {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.skill-item {
  padding: 8px 10px;
  margin-bottom: 4px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  transition: border-color 0.15s ease;
}

.skill-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 10px;
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  font-size: 11px;
  color: var(--el-color-primary);
  cursor: pointer;
  line-height: 1;
  flex-shrink: 0;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.detail-btn:hover {
  background: color-mix(in srgb, var(--el-color-primary) 15%, transparent);
  border-color: var(--el-color-primary-light-3);
  box-shadow: 0 1px 4px color-mix(in srgb, var(--el-color-primary) 12%, transparent);
}

.detail-btn:active {
  transform: scale(0.95);
  background: color-mix(in srgb, var(--el-color-primary) 20%, transparent);
}

.skill-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-color-primary);
  transition: color 0.15s ease, opacity 0.15s ease;
}

.code-agent-hint .hint-sub {
  line-height: 1.45;
}

.code-agent-box {
  border: 1px solid var(--el-color-primary-light-7);
  background: color-mix(in srgb, var(--el-color-primary) 7%, var(--el-fill-color-light));
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
