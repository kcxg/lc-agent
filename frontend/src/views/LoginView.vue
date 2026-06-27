<template>
  <main class="login-view">
    <canvas
      ref="canvasRef"
      class="login-canvas"
      aria-hidden="true"
    />

    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-heading">
        <p class="login-brand" id="login-title">→ sreagent</p>
        <p class="login-subtitle">智能运维控制中心</p>
      </div>

      <div
        v-if="errorMessage"
        class="login-error"
        role="alert"
      >
        <span class="login-error-text">{{ errorMessage }}</span>
      </div>

      <el-form
        class="login-form"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item>
          <template #label>
            <span class="form-label">用户名</span>
          </template>
          <el-input
            v-model.trim="username"
            class="login-input"
            autocomplete="username"
            placeholder="请输入用户名"
            :disabled="isSubmitting"
          />
        </el-form-item>

        <el-form-item>
          <template #label>
            <span class="form-label">密码</span>
          </template>
          <el-input
            v-model="password"
            class="login-input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="isSubmitting"
            show-password
          />
        </el-form-item>

        <el-button
          class="login-submit"
          native-type="submit"
          :loading="isSubmitting"
        >
          {{ isSubmitting ? '验证中...' : '登录' }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

const redirectPath = computed(() => {
  const redirect = route.query.redirect
  return typeof redirect === 'string' && redirect.startsWith('/') ? redirect : '/'
})

async function handleSubmit() {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await authStore.login(username.value, password.value)
    await router.replace(redirectPath.value)
  } catch {
    errorMessage.value = '登录失败，请检查账号密码后重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--el-bg-color-page);
}

.login-panel {
  width: min(100%, 380px);
  padding: 28px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-bg-color);
  box-shadow: var(--el-box-shadow-light);
}

.login-heading {
  margin-bottom: 22px;
}

.login-heading h1 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 650;
  color: var(--el-text-color-primary);
}

.login-heading p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.login-error {
  margin-bottom: 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
}

.login-submit {
  width: 100%;
  margin-top: 6px;
}
</style>
