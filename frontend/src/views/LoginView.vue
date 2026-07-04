<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <template #header>
        <div class="login-header">
          <span class="login-logo">⚡</span>
          <h1>登录</h1>
        </div>
      </template>

      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" style="margin-bottom: 16px" />

        <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  if (authStore.authRequired === null) {
    await authStore.checkBackendAuth()
  }
  if (!authStore.authRequired) {
    await router.push('/')
  }
})

async function handleLogin() {
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''
  try {
    await authStore.login(username.value.trim(), password.value)
    await router.push('/')
  } catch (e: any) {
    error.value = e.message || '认证失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  background: var(--el-bg-color-page);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
}

.login-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.login-logo {
  font-size: 24px;
}

.login-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>
