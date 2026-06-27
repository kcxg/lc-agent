import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ChatView,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/c/:sessionId',
      name: 'chat',
      component: ChatView,
      props: true,
    },
    {
      path: '/test-segments',
      name: 'test-segments',
      component: () => import('@/views/TestSegments.vue'),
    },
  ],
})

router.beforeEach(async to => {
  const authStore = useAuthStore()

  if (!authStore.initialized) {
    await authStore.refreshAuth()
  }

  if (to.meta.public) {
    if (to.name === 'login' && authStore.authenticated) {
      const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/'
      return redirect === to.fullPath ? '/' : redirect
    }
    return true
  }

  if (!authStore.authenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  return true
})

export default router
