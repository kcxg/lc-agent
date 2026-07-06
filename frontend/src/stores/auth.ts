import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<{ id: string; username: string; role: string } | null>(null)
  const authRequired = ref<boolean | null>(null)
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function checkBackendAuth(): Promise<boolean> {
    try {
      const resp = await fetch('/api/health')
      const data = await resp.json()
      const enabled = data.auth_enabled ?? false
      authRequired.value = enabled
      return enabled
    } catch {
      authRequired.value = false
      return false
    }
  }

  async function login(username: string, password: string) {
    const resp = await apiLogin(username, password)
    token.value = resp.token
    user.value = resp.user
    localStorage.setItem('token', resp.token)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    try {
      user.value = await getMe(token.value)
      return true
    } catch {
      logout()
      return false
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('auth:expired', () => {
      logout()
      window.location.hash = '#/login'
    })
  }

  return {
    token,
    user,
    authRequired,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    checkAuth,
    checkBackendAuth,
  }
})
