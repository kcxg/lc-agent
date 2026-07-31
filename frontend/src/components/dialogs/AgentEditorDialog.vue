<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑 Agent' : '新建 Agent'"
    width="720px"
    class="agent-editor-dialog"
    :close-on-click-modal="false"
  >
    <el-alert v-if="isCodeAgent" type="warning" :closable="false" style="margin-bottom: 12px">
      此智能体由代码注册（CompiledGraph），工具、MCP、Skills、提示词和模型由代码中的 graph 决定。此处仅展示说明，不能修改框架级配置。
    </el-alert>

    <el-form v-if="!isCodeAgent" :model="form" label-width="100px" label-position="top">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本设置" name="basic">
      <el-form-item class="project-mode-field project-mode-field--toggle">
        <div class="project-mode-toggle-row">
          <el-checkbox v-model="form.project_mode" :disabled="isCodeAgent">
            <span class="project-mode-label">
              <el-icon class="project-mode-label-icon"><Folder /></el-icon>
              项目模式
            </span>
          </el-checkbox>
          <el-tag v-if="form.project_mode" type="warning" size="small" style="margin-left: 8px;">项目</el-tag>
          <el-button
            type="info"
            text
            size="small"
            class="project-help-btn"
            style="margin-left: 4px;"
            @click="showProjectModeHelp = true"
          >
            <el-icon><QuestionFilled /></el-icon>
          </el-button>
        </div>
        <div class="form-hint">
          开启后自动注入 AGENTS.md、git 快照、OS 信息等项目上下文到系统提示词
        </div>
      </el-form-item>

      <el-form-item v-if="form.project_mode" label="项目根目录" class="project-mode-field">
        <div class="project-root-row">
          <el-input
            v-model="form.project_root"
            :disabled="isCodeAgent"
            placeholder="如 D:\\codes\\my-project"
            clearable
          />
        </div>
        <div class="form-hint">
          自动加载项目 AGENTS.md、Skills 和 MCP，文件工具默认限制在此目录
        </div>
      </el-form-item>

      <el-form-item v-if="form.project_mode && form.project_root" label="额外允许目录" class="project-mode-field">
        <el-input
          v-model="projectExtraDirsText"
          :disabled="isCodeAgent"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="除项目目录外允许访问的其他路径，每行一个（可选）"
        />
        <div class="form-hint">项目模式下文件工具默认只能访问项目目录，此处可追加其他允许路径</div>
      </el-form-item>

      <el-form-item label="名称" required>
        <el-input v-model="form.name" :disabled="isCodeAgent" placeholder="例如：code-assistant、researcher" />
        <div class="form-hint">只能使用英文字母、数字、连字符(-)和下划线(_)，且必须以字母开头</div>
      </el-form-item>

      <el-form-item label="显示名称">
        <el-input v-model="form.display_name" :disabled="isCodeAgent" placeholder="可填中文，例如：代码助手（留空则显示名称字段）" />
      </el-form-item>

      <el-form-item label="模型">
        <el-select v-model="form.default_model" :disabled="isCodeAgent" filterable style="width:100%" placeholder="选择默认模型">
          <el-option
            v-for="model in toolsStore.models"
            :key="model.id"
            :label="`${model.id} (${model.provider})`"
            :value="model.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="Temperature">
        <div class="llm-param-item">
          <el-checkbox
            :model-value="form.llm_params?.temperature !== undefined"
            :disabled="isCodeAgent"
            @update:model-value="toggleTemperature"
          >为此预设固定温度值</el-checkbox>
          <div v-if="form.llm_params?.temperature !== undefined" class="temperature-preset-control">
            <el-slider
              :model-value="form.llm_params.temperature"
              :min="0"
              :max="2"
              :step="0.05"
              :disabled="isCodeAgent"
              class="temp-slider"
              @update:model-value="setTemperature"
            />
            <el-input-number
              :model-value="form.llm_params.temperature"
              :min="0"
              :max="2"
              :step="0.05"
              :precision="2"
              size="small"
              controls-position="right"
              :disabled="isCodeAgent"
              style="width: 80px"
              @update:model-value="setTemperature"
            />
          </div>
          <span v-else class="param-hint">留空时运行时默认 0.7</span>
        </div>
      </el-form-item>

      <el-form-item label="思考级别（reasoning_effort）">
        <div class="llm-param-item">
          <el-checkbox
            :model-value="form.llm_params?.reasoning_effort !== undefined"
            :disabled="isCodeAgent"
            @update:model-value="toggleReasoningEffort"
          >为此预设固定思考级别</el-checkbox>
          <el-select
            v-if="form.llm_params?.reasoning_effort !== undefined"
            :model-value="form.llm_params.reasoning_effort"
            size="small"
            :disabled="isCodeAgent"
            style="width: 140px; margin-top: 6px"
            @update:model-value="setReasoningEffort"
          >
            <el-option
              v-for="effort in REASONING_EFFORTS"
              :key="effort"
              :label="effort"
              :value="effort"
            />
          </el-select>
          <span v-else class="param-hint">留空时由模型决定</span>
        </div>
      </el-form-item>

      <el-form-item label="系统提示词">
        <el-input
          v-model="form.system_prompt"
          :disabled="isCodeAgent"
          type="textarea"
          :autosize="{ minRows: 4, maxRows: 12 }"
          placeholder="定义 Agent 的行为和角色..."
        />
      </el-form-item>

      <el-form-item label="允许的工具组">
        <div class="tool-group-select">
          <el-radio-group v-model="toolGroupMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="toolGroupMode === 'custom'" class="custom-groups">
            <el-checkbox-group v-model="selectedGroups">
              <el-checkbox
                v-for="group in toolsStore.groups"
                :key="group.id"
                :value="group.id"
              >
                {{ group.description || group.id }} ({{ group.tools.length }} tools)
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>

      <el-form-item label="允许的 MCP 服务器">
        <div class="tool-group-select">
          <el-radio-group v-model="mcpMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="mcpMode === 'custom'" class="custom-groups">
            <el-checkbox-group v-model="selectedMcpServers">
              <el-checkbox
                v-for="server in toolsStore.mcpServers"
                :key="server.name"
                :value="server.name"
              >
                {{ server.name }}
                <el-tag size="small" :type="server.status === 'connected' ? 'success' : 'info'" style="margin-left:4px">
                  {{ server.tools?.length || 0 }} tools
                </el-tag>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>

      <!-- 全局 Skills -->
      <el-form-item label="允许的全局 Skills">
        <div class="tool-group-select">
          <el-radio-group v-model="globalSkillsMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="globalSkillsMode === 'custom'" v-loading="dialogSkillsLoading" class="custom-groups">
            <el-checkbox-group v-model="selectedGlobalSkills">
              <el-checkbox
                v-for="skill in dialogGlobalSkills"
                :key="skill.name"
                :value="skill.name"
              >
                {{ skill.name }}
                <span class="skill-hint">{{ skill.description }}</span>
              </el-checkbox>
              <div v-if="dialogGlobalSkills.length === 0" class="skill-empty-tip">暂无全局 Skills</div>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>

      <!-- 项目级 Skills（仅当项目模式开启且存在项目 skills 时显示） -->
      <el-form-item v-if="form.project_mode && dialogProjectSkills.length > 0" label="允许的项目 Skills">
        <div class="form-hint" style="margin-bottom: 6px;">{{ form.project_root }}/.agents/skills/</div>
        <div class="tool-group-select">
          <el-radio-group v-model="projectSkillsMode" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="none">无</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <div v-if="projectSkillsMode === 'custom'" v-loading="dialogSkillsLoading" class="custom-groups">
            <el-checkbox-group v-model="selectedProjectSkills">
              <el-checkbox
                v-for="skill in dialogProjectSkills"
                :key="skill.name"
                :value="skill.name"
              >
                {{ skill.name }}
                <span class="skill-hint">{{ skill.description }}</span>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="子Agent" name="subagents">
          <div class="subagent-picker">
            <div class="general-purpose-subagent">
              <el-checkbox v-model="form.enable_general_purpose_subagent">
                <span style="font-weight: 600;">启用通用子 Agent</span>
              </el-checkbox>
              <p class="picker-hint" style="font-size:12px; color: var(--el-text-color-secondary); margin: 4px 0 12px 24px;">
                让当前 Agent 可以把复杂任务委派给一个同能力的隔离 worker。该 worker 不会继续调用 task。
              </p>
            </div>
            <p class="picker-hint" style="font-size:12px; color: var(--el-text-color-secondary); margin-bottom: 12px;">
              选择专业子 Agent，并为每个子 Agent 填写委派说明。
            </p>
            <div class="subagent-list">
              <div
                v-for="sa in availableSubagents"
                :key="sa.id"
                class="subagent-item"
              >
                <el-checkbox
                  :model-value="isSubagentSelected(sa.id)"
                  @update:model-value="toggleSubagent(sa.id, $event)"
                >
                  <span class="sa-item-name" style="font-weight: 600;">{{ sa.display_name || sa.name }}</span>
                  <el-tag
                    size="small"
                    :type="sa.source === 'code' ? 'info' : sa.source === 'builtin' ? 'warning' : 'primary'"
                    style="margin-left: 6px;"
                  >
                    {{ sa.source }}
                  </el-tag>
                </el-checkbox>
                <span v-if="sa.description" class="sa-item-desc">
                  {{ sa.description }}
                </span>
                <div v-if="isSubagentSelected(sa.id)" class="subagent-delegation-section">
                  <p class="subagent-delegation-help">
                    填写该子 Agent 适合处理什么任务，以便主 Agent 能在正确、合适的时机触发调用它，作用类似 Skill 的 description；不能为空。
                  </p>
                  <el-input
                    :model-value="getSubagentDelegationDescription(sa.id)"
                    type="textarea"
                    :autosize="{ minRows: 2, maxRows: 4 }"
                    placeholder="例如：当对话涉及数据分析、报表生成时调用它"
                    class="subagent-delegation-input"
                    @update:model-value="setSubagentDelegationDescription(sa.id, $event)"
                  />
                </div>
              </div>
            </div>
            <el-empty
              v-if="availableSubagents.length === 0"
              description="暂无可用的子 Agent"
              :image-size="60"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-form>

    <div v-else class="code-agent-readonly">
      <div class="readonly-row">
        <span class="readonly-label">名称</span>
        <span class="readonly-value">{{ form.name }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">说明</span>
        <span class="readonly-value">{{ form.system_prompt }}</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">运行模型</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
      <div class="readonly-row">
        <span class="readonly-label">工具能力</span>
        <span class="readonly-value">由代码 graph 决定</span>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="danger" v-if="isEdit && !agentsStore.isAgentBuiltin(editingId!) && !isCodeAgent" @click="handleDelete">
        删除
      </el-button>
      <el-button v-if="!isCodeAgent" type="primary" :loading="saving" @click="handleSave">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 项目文件夹模式说明弹窗 -->
  <el-dialog
    v-model="showProjectModeHelp"
    title="项目文件夹模式说明"
    width="520px"
    :append-to-body="true"
  >
    <div class="project-mode-help">
      <p>开启"项目模式"后，该 Agent 将以项目文件夹为中心运行，类似 Cursor / Codex 打开一个项目的体验：</p>
      <ul>
        <li><strong>项目上下文注入</strong> — 自动将 git 状态快照、当前分支、最近提交、OS 信息注入系统提示词</li>
        <li><strong>AGENTS.md 注入</strong> — 自动读取 <code>{project_root}/AGENTS.md</code> 作为系统指令的一部分</li>
        <li><strong>项目 Skills</strong> — 自动加载 <code>{project_root}/.agents/skills/</code> 下的技能定义</li>
        <li><strong>项目 MCP</strong> — 自动连接 <code>{project_root}/.agents/mcp.json</code> 中声明的 MCP 服务</li>
        <li><strong>文件工具范围</strong> — 文件读写工具默认只能访问项目目录（及"额外允许目录"）</li>
        <li><strong>命令工作目录</strong> — <code>run_command</code> 的默认 CWD 为项目根目录</li>
      </ul>
      <p style="margin-top: 8px; color: var(--el-text-color-secondary); font-size: 12px;">
        git 状态是会话开始时的快照，如需刷新可让 Agent 执行 <code>run_command</code> 更新。
      </p>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { QuestionFilled, Folder } from '@element-plus/icons-vue'
import { fetchAvailableSubagents, api } from '@/api/http'
import { useToolsStore } from '@/stores/tools'
import { useAgentsStore, type AgentPreset, type AgentSubagentConfig } from '@/stores/agents'

const REASONING_EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh']

const toolsStore = useToolsStore()
const agentsStore = useAgentsStore()

const visible = ref(false)
const saving = ref(false)
const activeTab = ref('basic')
const isEdit = ref(false)
const editingId = ref('')
const editingSource = ref<'builtin' | 'code' | 'user'>('user')
const toolGroupMode = ref<'all' | 'none' | 'custom'>('all')
const selectedGroups = ref<string[]>([])
const mcpMode = ref<'all' | 'none' | 'custom'>('all')
const selectedMcpServers = ref<string[]>([])
const globalSkillsMode = ref<'all' | 'none' | 'custom'>('all')
const selectedGlobalSkills = ref<string[]>([])
const projectSkillsMode = ref<'all' | 'none' | 'custom'>('all')
const selectedProjectSkills = ref<string[]>([])
const availableSubagents = ref<Array<{ id: string; name: string; display_name: string | null; source: string; description: string }>>([])

const isCodeAgent = ref(false)
const showProjectModeHelp = ref(false)

// Dialog-local skill lists, fetched on open and when project_root changes
type DialogSkill = { name: string; description: string; scope: 'global' | 'project'; enabled: boolean }
const dialogAllSkills = ref<DialogSkill[]>([])
const dialogSkillsLoading = ref(false)
const dialogGlobalSkills = computed(() => dialogAllSkills.value.filter(s => s.scope === 'global'))
const dialogProjectSkills = computed(() => dialogAllSkills.value.filter(s => s.scope === 'project'))

let _skillFetchSeq = 0  // request sequence to avoid stale response overwriting newer result

async function fetchDialogSkills() {
  const seq = ++_skillFetchSeq
  dialogSkillsLoading.value = true
  try {
    const projectRoot = (form.value.project_mode && form.value.project_root.trim()) ? form.value.project_root.trim() : undefined
    const result = await api.getSkills(projectRoot)
    if (seq !== _skillFetchSeq) return  // stale response; a newer request is in-flight
    dialogAllSkills.value = result
    // Prune stale selections that no longer exist in the fetched list
    const globalNames = new Set(result.filter((s: any) => s.scope === 'global').map((s: any) => s.name))
    const projectNames = new Set(result.filter((s: any) => s.scope === 'project').map((s: any) => s.name))
    selectedGlobalSkills.value = selectedGlobalSkills.value.filter(n => globalNames.has(n))
    selectedProjectSkills.value = selectedProjectSkills.value.filter(n => projectNames.has(n))
  } catch (e) {
    if (seq !== _skillFetchSeq) return
    console.error('[AgentEditorDialog] Failed to fetch skills:', e)
    dialogAllSkills.value = []
    ElMessage.warning('加载 Skills 列表失败，请检查后端服务')
  } finally {
    if (seq === _skillFetchSeq) dialogSkillsLoading.value = false
  }
}

const form = ref({
  name: '',
  display_name: '',
  system_prompt: '',
  default_model: '',
  llm_params: null as Record<string, any> | null,
  subagents: [] as AgentSubagentConfig[],
  enable_general_purpose_subagent: false,
  project_mode: false,
  project_root: '',
  project_extra_dirs: null as string[] | null,
})

const projectExtraDirsText = computed({
  get: () => (form.value.project_extra_dirs || []).join('\n'),
  set: (val: string) => {
    const lines = val.split('\n').map(l => l.trim()).filter(Boolean)
    form.value.project_extra_dirs = lines.length > 0 ? lines : null
  },
})

// Re-fetch skills when project_root or project_mode changes
let _skillFetchTimer: ReturnType<typeof setTimeout> | null = null
watch([() => form.value.project_root, () => form.value.project_mode], () => {
  if (!visible.value) return
  projectSkillsMode.value = 'all'
  selectedProjectSkills.value = []
  if (_skillFetchTimer) clearTimeout(_skillFetchTimer)
  _skillFetchTimer = setTimeout(() => {
    _skillFetchTimer = null
    fetchDialogSkills()
  }, 400)
})

function _distributeAllowedSkills(allowedSkills: string[] | null) {
  const globalNames = new Set(dialogGlobalSkills.value.map(s => s.name))
  const projectNames = new Set(dialogProjectSkills.value.map(s => s.name))
  const hasProject = projectNames.size > 0

  if (allowedSkills === null) {
    globalSkillsMode.value = 'all'
    selectedGlobalSkills.value = []
    projectSkillsMode.value = 'all'
    selectedProjectSkills.value = []
    return
  }
  if (allowedSkills.length === 0) {
    globalSkillsMode.value = 'none'
    selectedGlobalSkills.value = []
    projectSkillsMode.value = 'none'
    selectedProjectSkills.value = []
    return
  }
  const allowedSet = new Set(allowedSkills)
  // Global section
  const allowedGlobal = [...globalNames].filter(n => allowedSet.has(n))
  if (allowedGlobal.length === 0) {
    globalSkillsMode.value = 'none'
    selectedGlobalSkills.value = []
  } else if (allowedGlobal.length === globalNames.size) {
    globalSkillsMode.value = 'all'
    selectedGlobalSkills.value = []
  } else {
    globalSkillsMode.value = 'custom'
    selectedGlobalSkills.value = allowedGlobal
  }
  // Project section
  if (!hasProject) {
    projectSkillsMode.value = 'all'
    selectedProjectSkills.value = []
    return
  }
  const allowedProject = [...projectNames].filter(n => allowedSet.has(n))
  if (allowedProject.length === 0) {
    projectSkillsMode.value = 'none'
    selectedProjectSkills.value = []
  } else if (allowedProject.length === projectNames.size) {
    projectSkillsMode.value = 'all'
    selectedProjectSkills.value = []
  } else {
    projectSkillsMode.value = 'custom'
    selectedProjectSkills.value = allowedProject
  }
}

function _computeAllowedSkills(): string[] | null {
  const hasProject = dialogProjectSkills.value.length > 0
  const effectiveProjectMode = hasProject ? projectSkillsMode.value : 'all'
  // Both all → no restriction
  if (globalSkillsMode.value === 'all' && effectiveProjectMode === 'all') return null

  const globalAllowed =
    globalSkillsMode.value === 'all' ? dialogGlobalSkills.value.map(s => s.name) :
    globalSkillsMode.value === 'none' ? [] :
    selectedGlobalSkills.value
  const projectAllowed = !hasProject ? [] :
    projectSkillsMode.value === 'all' ? dialogProjectSkills.value.map(s => s.name) :
    projectSkillsMode.value === 'none' ? [] :
    selectedProjectSkills.value
  return [...globalAllowed, ...projectAllowed]
}

async function open(agent?: AgentPreset) {
  activeTab.value = 'basic'

  // Set form values first (project_root needed before fetchDialogSkills)
  if (agent) {
    isEdit.value = true
    editingId.value = agent.id
    editingSource.value = agent.source || 'user'
    isCodeAgent.value = agent.source === 'code'
    form.value.name = agent.name
    form.value.display_name = agent.display_name ?? ''
    form.value.system_prompt = agent.system_prompt
    form.value.default_model = agent.default_model
    form.value.llm_params = agent.llm_params ?? null
    form.value.subagents = agent.subagents ? agent.subagents.map(item => ({ ...item })) : []
    form.value.enable_general_purpose_subagent = agent.enable_general_purpose_subagent ?? false
    form.value.project_mode = agent.project_mode ?? false
    form.value.project_root = agent.project_root ?? ''
    form.value.project_extra_dirs = agent.project_extra_dirs ?? null
  } else {
    isEdit.value = false
    editingId.value = ''
    editingSource.value = 'user'
    isCodeAgent.value = false
    form.value = {
      name: '',
      display_name: '',
      system_prompt: '',
      default_model: toolsStore.currentModel,
      llm_params: null,
      subagents: [],
      enable_general_purpose_subagent: false,
      project_mode: false,
      project_root: '',
      project_extra_dirs: null,
    }
  }

  // Fetch skills and subagents in parallel (skills need project_root set above)
  const [allSubagents] = await Promise.all([
    fetchAvailableSubagents(),
    fetchDialogSkills(),
  ])
  availableSubagents.value = allSubagents.filter(sa => sa.id !== (agent?.id ?? ''))

  // Tool groups & MCP: simple three-state
  if (agent) {
    if (agent.allowed_tool_groups === null) {
      toolGroupMode.value = 'all'; selectedGroups.value = []
    } else if (agent.allowed_tool_groups.length === 0) {
      toolGroupMode.value = 'none'; selectedGroups.value = []
    } else {
      toolGroupMode.value = 'custom'; selectedGroups.value = [...agent.allowed_tool_groups]
    }
    if (agent.allowed_mcp_servers === null) {
      mcpMode.value = 'all'; selectedMcpServers.value = []
    } else if (agent.allowed_mcp_servers.length === 0) {
      mcpMode.value = 'none'; selectedMcpServers.value = []
    } else {
      mcpMode.value = 'custom'; selectedMcpServers.value = [...agent.allowed_mcp_servers]
    }
    // Distribute allowed_skills into global + project sections now that skills are loaded
    _distributeAllowedSkills(agent.allowed_skills)
  } else {
    toolGroupMode.value = 'none'; selectedGroups.value = []
    mcpMode.value = 'none'; selectedMcpServers.value = []
    globalSkillsMode.value = 'none'; selectedGlobalSkills.value = []
    projectSkillsMode.value = 'none'; selectedProjectSkills.value = []
  }

  visible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const namePattern = /^[a-zA-Z][a-zA-Z0-9_-]*$/
    if (!namePattern.test(form.value.name)) {
      ElMessage.error('名称只能使用英文字母、数字、连字符(-)和下划线(_)，且必须以字母开头')
      return
    }

    const allowed_tool_groups =
      toolGroupMode.value === 'all' ? null :
      toolGroupMode.value === 'none' ? [] :
      selectedGroups.value

    const allowed_mcp_servers =
      mcpMode.value === 'all' ? null :
      mcpMode.value === 'none' ? [] :
      selectedMcpServers.value

    const allowed_skills = _computeAllowedSkills()

    if (form.value.project_mode && !form.value.project_root.trim()) {
      ElMessage.error('开启项目模式时，必须填写项目根目录')
      return
    }

    if (form.value.project_mode) {
      const FILE_TOOL_GROUPS = ['file_read', 'file_write', 'command']
      const hasFileTools =
        toolGroupMode.value === 'all' ||
        (toolGroupMode.value === 'custom' && selectedGroups.value.some(g => FILE_TOOL_GROUPS.includes(g)))
      if (!hasFileTools) {
        activeTab.value = 'basic'
        ElMessage.error('项目模式需要至少启用 file_read、file_write 或 command 工具组之一')
        return
      }
    }

    if (form.value.subagents.some(item => !item.delegation_description.trim())) {
      activeTab.value = 'subagents'
      ElMessage.error('每个已选择的子 Agent 都必须填写非空的委派说明')
      return
    }

    const normalizedSubagents = form.value.subagents.map(item => ({
      agent_id: item.agent_id,
      delegation_description: item.delegation_description.trim(),
    }))

    const data = {
      name: form.value.name,
      display_name: form.value.display_name || null,
      system_prompt: form.value.system_prompt,
      default_model: form.value.default_model,
      allowed_tool_groups,
      allowed_mcp_servers,
      allowed_skills,
      llm_params: form.value.llm_params || null,
      subagents: normalizedSubagents.length > 0 ? normalizedSubagents : null,
      enable_general_purpose_subagent: form.value.enable_general_purpose_subagent,
      project_mode: form.value.project_mode,
      project_root: form.value.project_mode ? (form.value.project_root || null) : null,
      project_extra_dirs: form.value.project_mode ? form.value.project_extra_dirs : null,
    }

    if (isEdit.value) {
      await agentsStore.updateAgent(editingId.value, data)
    } else {
      await agentsStore.createAgent(data as any)
    }
    visible.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  await agentsStore.deleteAgent(editingId.value)
  visible.value = false
}

function isSubagentSelected(agentId: string) {
  return form.value.subagents.some(item => item.agent_id === agentId)
}

function getSubagentDelegationDescription(agentId: string) {
  return form.value.subagents.find(item => item.agent_id === agentId)?.delegation_description || ''
}

function toggleSubagent(agentId: string, checked: boolean | string | number) {
  if (checked) {
    if (!isSubagentSelected(agentId)) {
      form.value.subagents.push({ agent_id: agentId, delegation_description: '' })
    }
    return
  }
  form.value.subagents = form.value.subagents.filter(item => item.agent_id !== agentId)
}

function setSubagentDelegationDescription(agentId: string, value: string | number) {
  const item = form.value.subagents.find(entry => entry.agent_id === agentId)
  if (!item) return
  item.delegation_description = String(value)
}

function _ensureLlmParams() {
  if (!form.value.llm_params) form.value.llm_params = {}
}

function _cleanLlmParams() {
  if (form.value.llm_params && !Object.keys(form.value.llm_params).length) {
    form.value.llm_params = null
  }
}

function toggleTemperature(v: boolean) {
  if (v) {
    _ensureLlmParams()
    form.value.llm_params!.temperature = 0.7
  } else {
    if (form.value.llm_params) {
      delete form.value.llm_params.temperature
      _cleanLlmParams()
    }
  }
}

function setTemperature(v: number | undefined) {
  if (v === undefined) return
  _ensureLlmParams()
  form.value.llm_params!.temperature = v
}

function toggleReasoningEffort(v: boolean) {
  if (v) {
    _ensureLlmParams()
    form.value.llm_params!.reasoning_effort = 'medium'
  } else {
    if (form.value.llm_params) {
      delete form.value.llm_params.reasoning_effort
      _cleanLlmParams()
    }
  }
}

function setReasoningEffort(v: string) {
  _ensureLlmParams()
  form.value.llm_params!.reasoning_effort = v
}

defineExpose({ open })
</script>

<style scoped>
.agent-editor-dialog :deep(.el-dialog__body) {
  max-height: min(68vh, 680px);
  overflow-y: auto;
  padding: 8px 20px 16px;
}

.agent-editor-dialog :deep(.el-dialog__header) {
  padding: 18px 24px 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.agent-editor-dialog :deep(.el-dialog__title) {
  font-size: 17px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.4px;
}

.agent-editor-dialog :deep(.el-dialog__footer) {
  padding: 12px 24px 16px;
}

.agent-editor-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.agent-editor-dialog :deep(.el-form-item:hover) {
  border-color: var(--el-border-color);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.agent-editor-dialog :deep(.el-form-item--label-top .el-form-item__label) {
  display: inline-flex !important;
  align-items: center;
  gap: 5px;
  width: auto !important;
  height: auto !important;
  padding: 5px 11px !important;
  margin-bottom: 10px !important;
  border-radius: 999px;
  background: var(--el-fill-color);
  border: 1px solid var(--el-border-color-light);
  font-size: 12px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3 !important;
  letter-spacing: 0.4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.agent-editor-dialog :deep(.el-form-item--label-top .el-form-item__label)::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-color-info);
  flex-shrink: 0;
}

.agent-editor-dialog :deep(.el-form-item--label-top.is-required .el-form-item__label) {
  padding-right: 11px !important;
}

.agent-editor-dialog :deep(.el-form-item--label-top.is-required .el-form-item__label)::after {
  content: '*';
  color: var(--el-color-danger);
  font-size: 12px;
  margin-left: 2px;
}

.agent-editor-dialog :deep(.el-form-item--label-top .el-form-item__label .el-form-item__asterisk) {
  display: none;
}

.agent-editor-dialog :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.agent-editor-dialog :deep(.el-tabs__content) {
  overflow: visible;
}

.agent-editor-dialog :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
  line-height: 1.5;
}

.llm-param-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.temperature-preset-control {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.temp-slider {
  flex: 1;
}

.param-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-left: 2px;
}

.tool-group-select {
  width: 100%;
}

.custom-groups {
  margin-top: 8px;
  padding: 10px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.custom-groups .el-checkbox {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.skill-hint {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-left: 4px;
  opacity: 0.7;
}

.skill-scope-header {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  padding: 4px 0 4px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 4px;
}

.skill-scope-header--project {
  margin-top: 10px;
}

.skill-scope-path {
  font-family: monospace;
  font-size: 10px;
  font-weight: normal;
  text-transform: none;
  letter-spacing: 0;
  color: var(--el-text-color-placeholder);
  margin-left: 4px;
}

.skill-empty-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  padding: 4px 0;
}

.subagent-picker {
  width: 100%;
}

@media (max-width: 760px) {
  .agent-editor-dialog :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
    margin-top: 6vh;
  }

  .agent-editor-dialog :deep(.el-dialog__body) {
    max-height: 74vh;
    padding-left: 16px;
    padding-right: 16px;
  }

  .agent-editor-dialog :deep(.el-dialog__header),
  .agent-editor-dialog :deep(.el-dialog__footer) {
    padding-left: 16px;
    padding-right: 16px;
  }
}

.subagent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.subagent-item {
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 10px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-extra-light);
}

.subagent-item :deep(.el-checkbox) {
  display: flex;
  align-items: center;
  height: auto;
  width: 100%;
}

.sa-item-desc {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-left: 22px;
  margin-top: 2px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.subagent-delegation-section {
  margin-top: 8px;
  margin-left: 22px;
  padding-right: 10px;
}

.subagent-delegation-help {
  margin-top: 0;
  margin-left: 0;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.subagent-delegation-input {
  margin-top: 0;
  margin-left: 0;
}

.code-agent-readonly {
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.readonly-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.readonly-row:last-child {
  border-bottom: none;
}

.readonly-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
}

.readonly-value {
  color: var(--el-text-color-primary);
  font-size: 13px;
  text-align: right;
}

:deep(.agent-editor-dialog) {
  max-width: min(600px, calc(100vw - 24px));
}

@media (max-width: 768px) {
  .subagent-item {
    padding: 10px 8px;
  }

  .sa-item-desc {
    margin-left: 0;
  }

  .subagent-delegation-section {
    margin-left: 0;
    padding-right: 0;
  }

  .subagent-delegation-help {
    margin-left: 0;
  }

  .subagent-delegation-input {
    margin-left: 0;
    width: 100%;
  }
}

.project-mode-field {
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-fill-color-extra-light) 100%);
  border-color: var(--el-color-primary-light-7);
}

.project-mode-field:hover {
  border-color: var(--el-color-primary-light-5);
}

.project-mode-field :deep(.el-form-item__label) {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.project-mode-field :deep(.el-form-item__label)::before {
  background: var(--el-color-primary);
}

.project-mode-field--toggle {
  border-left-width: 4px;
  border-left-color: var(--el-color-primary);
}

.project-mode-toggle-row {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 2px 0;
}

.project-mode-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 14px;
  color: var(--el-color-primary);
}

.project-mode-label-icon {
  font-size: 16px;
}

.project-root-row {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.project-root-row .el-input {
  flex: 1;
}

.project-help-btn {
  flex-shrink: 0;
  padding: 4px 6px;
}

.project-mode-help {
  font-size: 14px;
  line-height: 1.8;
}

.project-mode-help ul {
  padding-left: 18px;
  margin: 8px 0;
}

.project-mode-help li {
  margin-bottom: 6px;
}

.project-mode-help code {
  background: var(--el-fill-color-light);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
}

</style>

<style>
.agent-editor-dialog .el-dialog__body {
  max-height: min(68vh, 680px);
  overflow-y: auto;
  padding: 8px 20px 16px;
}

.agent-editor-dialog .el-dialog__header {
  padding: 18px 24px 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.agent-editor-dialog .el-dialog__title {
  font-size: 17px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: 0.4px;
}

.agent-editor-dialog .el-dialog__footer {
  padding: 12px 24px 16px;
}

.agent-editor-dialog .el-form-item {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.agent-editor-dialog .el-form-item:hover {
  border-color: var(--el-border-color);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.agent-editor-dialog .el-form-item--label-top .el-form-item__label {
  display: inline-flex !important;
  align-items: center;
  gap: 5px;
  width: auto !important;
  height: auto !important;
  padding: 5px 11px !important;
  margin-bottom: 10px !important;
  border: 1px solid var(--el-border-color-light);
  border-radius: 999px;
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.3 !important;
  letter-spacing: 0.4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.agent-editor-dialog .el-form-item--label-top .el-form-item__label::before {
  content: '';
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--el-color-info);
}

.agent-editor-dialog .el-form-item--label-top.is-required .el-form-item__label::after {
  content: '*';
  margin-left: 2px;
  color: var(--el-color-danger);
  font-size: 12px;
}

.agent-editor-dialog .el-form-item--label-top .el-form-item__label .el-form-item__asterisk {
  display: none;
}

.agent-editor-dialog .project-mode-field {
  border-color: var(--el-color-primary-light-7);
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-fill-color-extra-light) 100%);
}

.agent-editor-dialog .project-mode-field:hover {
  border-color: var(--el-color-primary-light-5);
}

.agent-editor-dialog .project-mode-field--toggle {
  border-left-width: 4px;
  border-left-color: var(--el-color-primary);
}

.agent-editor-dialog .project-mode-field .el-form-item__label {
  border-color: var(--el-color-primary-light-7);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.agent-editor-dialog .project-mode-field .el-form-item__label::before {
  background: var(--el-color-primary);
}

@media (max-width: 760px) {
  .agent-editor-dialog {
    width: calc(100vw - 24px) !important;
    margin-top: 6vh;
  }

  .agent-editor-dialog .el-dialog__body {
    max-height: 74vh;
    padding-right: 16px;
    padding-left: 16px;
  }

  .agent-editor-dialog .el-dialog__header,
  .agent-editor-dialog .el-dialog__footer {
    padding-right: 16px;
    padding-left: 16px;
  }
}
</style>
