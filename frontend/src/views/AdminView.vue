<template>
  <div class="admin-page">
    <el-card shadow="never">
      <template #header>
        <div class="admin-header">
          <h2>用户管理</h2>
          <div class="admin-actions">
            <el-button @click="router.push('/')">返回首页</el-button>
            <el-button type="primary" @click="openCreateDialog">创建用户</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="users" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openAgentsDialog(row)">Agent 授权</el-button>
            <el-button size="small" type="warning" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.role === 'admin'"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create user dialog -->
    <el-dialog v-model="createVisible" title="创建用户" width="420px" :close-on-click-modal="false">
      <el-form @submit.prevent="handleCreate">
        <el-form-item label="用户名">
          <el-input v-model="newUsername" placeholder="输入用户名" autocomplete="off" />
        </el-form-item>
      </el-form>
      <el-alert v-if="createError" :title="createError" type="error" show-icon :closable="false" style="margin-bottom: 12px" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- Generated password dialog -->
    <el-dialog v-model="passwordVisible" title="生成的密码" width="420px" :close-on-click-modal="false">
      <p class="password-hint">请妥善保存以下密码，关闭后将无法再次查看：</p>
      <el-input :model-value="generatedPassword" readonly>
        <template #append>
          <el-button @click="copyPassword">复制</el-button>
        </template>
      </el-input>
      <template #footer>
        <el-button type="primary" @click="passwordVisible = false">已保存</el-button>
      </template>
    </el-dialog>

    <!-- Agent authorization dialog -->
    <el-dialog
      v-model="agentsVisible"
      :title="`Agent 授权 — ${selectedUser?.username || ''}`"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-checkbox-group v-model="selectedAgentIds" class="agent-checkboxes">
        <el-checkbox v-for="agent in agents" :key="agent.id" :value="agent.id" :label="agent.id">
          {{ agent.display_name || agent.name }}
          <el-tag size="small" style="margin-left: 6px">{{ agent.source || 'user' }}</el-tag>
        </el-checkbox>
      </el-checkbox-group>
      <el-alert v-if="agentsError" :title="agentsError" type="error" show-icon :closable="false" style="margin-top: 12px" />
      <template #footer>
        <el-button @click="agentsVisible = false">取消</el-button>
        <el-button type="primary" :loading="agentsLoading" @click="handleSaveAgents">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchApi, api } from '@/api/http'

interface AdminUser {
  id: string
  username: string
  role: string
  created_at: string
}

interface AgentItem {
  id: string
  name: string
  display_name?: string | null
  source?: string
}

const router = useRouter()
const users = ref<AdminUser[]>([])
const agents = ref<AgentItem[]>([])
const loading = ref(false)

const createVisible = ref(false)
const createLoading = ref(false)
const createError = ref('')
const newUsername = ref('')

const passwordVisible = ref(false)
const generatedPassword = ref('')

const agentsVisible = ref(false)
const agentsLoading = ref(false)
const agentsError = ref('')
const selectedUser = ref<AdminUser | null>(null)
const selectedAgentIds = ref<string[]>([])

onMounted(async () => {
  await Promise.all([loadUsers(), loadAgents()])
})

async function loadUsers() {
  loading.value = true
  try {
    users.value = await fetchApi<AdminUser[]>('/admin/users')
  } catch (e: any) {
    ElMessage.error(e.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    agents.value = await api.getAgents()
  } catch (e: any) {
    ElMessage.error(e.message || '加载 Agent 列表失败')
  }
}

function formatDate(iso: string): string {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

function openCreateDialog() {
  newUsername.value = ''
  createError.value = ''
  createVisible.value = true
}

async function handleCreate() {
  const username = newUsername.value.trim()
  if (!username) {
    createError.value = '请输入用户名'
    return
  }

  createLoading.value = true
  createError.value = ''
  try {
    const result = await fetchApi<{ password: string }>('/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username }),
    })
    createVisible.value = false
    generatedPassword.value = result.password
    passwordVisible.value = true
    await loadUsers()
    ElMessage.success('用户创建成功')
  } catch (e: any) {
    createError.value = e.message || '创建失败'
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(user: AdminUser) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await fetchApi<void>(`/admin/users/${user.id}`, { method: 'DELETE' })
    ElMessage.success('用户已删除')
    await loadUsers()
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

async function handleResetPassword(user: AdminUser) {
  try {
    await ElMessageBox.confirm(`确定重置用户「${user.username}」的密码？`, '确认重置', {
      type: 'warning',
      confirmButtonText: '重置',
      cancelButtonText: '取消',
    })
    const result = await fetchApi<{ password: string }>(`/admin/users/${user.id}/reset-password`, {
      method: 'PUT',
    })
    generatedPassword.value = result.password
    passwordVisible.value = true
  } catch (e: any) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error(e.message || '重置失败')
    }
  }
}

async function openAgentsDialog(user: AdminUser) {
  selectedUser.value = user
  agentsError.value = ''
  agentsVisible.value = true
  agentsLoading.value = true
  try {
    const result = await fetchApi<{ agent_ids: string[] }>(`/admin/users/${user.id}/agents`)
    selectedAgentIds.value = result.agent_ids
  } catch (e: any) {
    agentsError.value = e.message || '加载授权失败'
    selectedAgentIds.value = []
  } finally {
    agentsLoading.value = false
  }
}

async function handleSaveAgents() {
  if (!selectedUser.value) return

  agentsLoading.value = true
  agentsError.value = ''
  try {
    await fetchApi(`/admin/users/${selectedUser.value.id}/agents`, {
      method: 'PUT',
      body: JSON.stringify({ agent_ids: selectedAgentIds.value }),
    })
    ElMessage.success('Agent 授权已保存')
    agentsVisible.value = false
  } catch (e: any) {
    agentsError.value = e.message || '保存失败'
  } finally {
    agentsLoading.value = false
  }
}

async function copyPassword() {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(generatedPassword.value)
      ElMessage.success('已复制到剪贴板')
      return
    } catch {
      // fall through to fallback
    }
  }

  const textarea = document.createElement('textarea')
  textarea.value = generatedPassword.value
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    if (document.execCommand('copy')) {
      ElMessage.success('已复制到剪贴板')
    } else {
      ElMessage.warning('复制失败，请手动复制')
    }
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  } finally {
    document.body.removeChild(textarea)
  }
}
</script>

<style scoped>
.admin-page {
  padding: 20px;
  overflow: auto;
  height: 100%;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.admin-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.admin-actions {
  display: flex;
  gap: 8px;
}

.password-hint {
  margin: 0 0 12px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.agent-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}
</style>
