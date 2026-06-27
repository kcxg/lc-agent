import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const initialized = ref(false)
  const authenticated = ref(false)
  const username = ref('')

  async function refreshAuth() {
    try {
      const state = await api.getAuthState()
      authenticated.value = state.authenticated
      username.value = state.username || ''
    } catch {
      authenticated.value = false
      username.value = ''
    } finally {
      initialized.value = true
    }
  }

  async function login(name: string, password: string) {
    const result = await api.login({ username: name, password })
    authenticated.value = result.authenticated
    username.value = result.username || ''
    initialized.value = true
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      authenticated.value = false
      username.value = ''
      initialized.value = true
    }
  }

  function markUnauthenticated() {
    authenticated.value = false
    username.value = ''
    initialized.value = true
  }

  return { initialized, authenticated, username, refreshAuth, login, logout, markUnauthenticated }
})
