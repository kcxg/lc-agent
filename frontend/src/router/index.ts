import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import LoginView from '@/views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/', name: 'home', component: ChatView },
    { path: '/c/:sessionId', name: 'chat', component: ChatView, props: true },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue'), meta: { requiresAdmin: true } },
    { path: '/test-segments', name: 'test-segments', component: () => import('@/views/TestSegments.vue') },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const authStore = useAuthStore()
  if (!authStore.isAuthenticated) {
    const valid = await authStore.checkAuth()
    if (!valid) return { name: 'login' }
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) return { name: 'home' }
  return true
})

export default router
