<template>
  <main class="login-view">
    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-heading">
        <h1 id="login-title">登录 lc-agent</h1>
        <p>请输入账号密码继续使用。</p>
      </div>

      <el-alert
        v-if="errorMessage"
        class="login-error"
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <el-form
        class="login-form"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名">
          <el-input
            v-model.trim="username"
            autocomplete="username"
            placeholder="请输入用户名"
            :disabled="isSubmitting"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            :disabled="isSubmitting"
            show-password
          />
        </el-form-item>

        <el-button
          class="login-submit"
          type="primary"
          native-type="submit"
          :loading="isSubmitting"
        >
          登录
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
