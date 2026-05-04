import { createRouter, createWebHistory } from 'vue-router'
import { authService } from '@/services/auth'
import { useAppStore } from '@/stores/appStore'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/uploads',
    name: 'Uploads',
    component: () => import('@/views/UploadsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/feedback-history',
    name: 'FeedbackHistory',
    component: () => import('@/views/FeedbackHistoryView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Route guard
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false
  const isAuthenticated = authService.isAuthenticated()
  const store = useAppStore()
  
  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/chat')
  } else {
    // 如果用户从登录页进入应用，确保初始化store
    if (from.path === '/login' && to.meta.requiresAuth) {
      if (!store.isInitialized) {
        store.init()
        store.isInitialized = true
      }
    }
    next()
  }
})

export default router
