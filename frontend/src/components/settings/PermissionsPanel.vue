<template>
  <div class="permissions-panel">
    <h3>工具权限白名单</h3>
    <p class="desc">白名单中的工具将跳过人工审批，自动执行。</p>

    <div class="allowlist">
      <el-tag
        v-for="tool in allowlist"
        :key="tool"
        closable
        @close="handleRemove(tool)"
        class="tool-tag"
      >
        {{ tool }}
      </el-tag>
      <el-tag v-if="allowlist.length === 0" type="info">（空 — 所有工具需要审批）</el-tag>
    </div>

    <div class="actions">
      <el-input
        v-model="newTool"
        placeholder="输入工具名添加到白名单"
        style="width: 280px"
        @keyup.enter="handleAdd"
      />
      <el-button type="primary" :disabled="!newTool.trim()" @click="handleAdd">添加</el-button>
      <el-button v-if="allowlist.length > 0" type="danger" plain @click="handleClearAll">清空全部</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getPermissions, allowTool, removeTool, setPermissions } from '@/api/permissions'
import { useChatStore } from '@/stores/chat'
import { ElMessage } from 'element-plus'

const allowlist = ref<string[]>([])
const newTool = ref('')
const chatStore = useChatStore()

async function fetchList() {
  try {
    const data = await getPermissions()
    allowlist.value = data.tool_allowlist
  } catch (e) {
    console.error('Failed to load permissions:', e)
  }
}

onMounted(fetchList)

watch(() => chatStore.isStreaming, (streaming, prev) => {
  if (prev && !streaming) {
    fetchList()
  }
})

async function handleAdd() {
  const name = newTool.value.trim()
  if (!name) return
  try {
    const data = await allowTool(name)
    allowlist.value = data.tool_allowlist
    newTool.value = ''
    ElMessage.success(`已添加 ${name} 到白名单`)
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function handleRemove(name: string) {
  try {
    const data = await removeTool(name)
    allowlist.value = data.tool_allowlist
    ElMessage.info(`已从白名单移除 ${name}`)
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

async function handleClearAll() {
  try {
    const data = await setPermissions([])
    allowlist.value = data.tool_allowlist
    ElMessage.warning('已清空全部白名单')
  } catch (e) {
    ElMessage.error('清空失败')
  }
}
</script>

<style scoped>
.permissions-panel {
  padding: 16px 0;
}
.desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.allowlist {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  min-height: 32px;
}
.tool-tag {
  font-family: 'JetBrains Mono', monospace;
}
.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
