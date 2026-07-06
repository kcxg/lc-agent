import { createRouter, createWebHashHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import { setUnauthorizedHandler } from '@/api/http'
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
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
    },
    {
      path: '/test-segments',
      name: 'test-segments',
      component: () => import('@/views/TestSegments.vue'),
    },
  ],
})

setUnauthorizedHandler(async () => {
  const authStore = useAuthStore()
  authStore.logout()
  await router.replace({
    path: '/login',
    query: { redirect: router.currentRoute.value.fullPath },
  })
})

router.beforeEach(async to => {
  const authStore = useAuthStore()

  if (authStore.authRequired === null) {
    await authStore.checkBackendAuth()
  }

  if (!authStore.authRequired) {
    return true
  }

  if (to.meta.public) {
    if (to.name === 'login' && authStore.isAuthenticated) {
      const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/'
      return redirect === to.fullPath ? '/' : redirect
    }
    return true
  }

  if (!authStore.isAuthenticated) {
    await authStore.checkAuth()
    if (!authStore.isAuthenticated) {
      return {
        path: '/login',
        query: { redirect: to.fullPath },
      }
    }
  }

  return true
})

export default router
