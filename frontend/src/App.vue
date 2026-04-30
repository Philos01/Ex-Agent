<template>
  <div class="min-h-screen bg-background text-on-surface">
    <!-- 移动端侧边栏遮罩 -->
    <div v-if="sidebarOpen && isMobile" class="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm" @click="sidebarOpen = false"></div>

    <!-- 深色侧边栏 (ChatGPT-style) -->
    <aside
      class="h-screen bg-inverse-surface text-inverse-on-surface flex flex-col py-5 z-50 transition-all duration-300"
      :class="[
        sidebarOpen || !isMobile ? 'translate-x-0' : '-translate-x-full',
        isMobile ? 'fixed left-0 top-0 w-72' : 'w-60 fixed left-0 top-0'
      ]"
    >
      <!-- Logo -->
      <div class="flex items-center gap-3 px-5 mb-6">
        <div class="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center">
          <span class="material-symbols-outlined text-primary-fixed">biotech</span>
        </div>
        <div>
          <h1 class="text-base font-bold text-inverse-on-surface leading-tight">Ex-Agent</h1>
          <p class="text-[10px] font-medium tracking-wider text-inverse-on-surface/40 uppercase">Laboratory OS</p>
        </div>
        <button v-if="isMobile" @click="sidebarOpen = false" class="ml-auto p-1.5 hover:bg-white/10 rounded-lg">
          <span class="material-symbols-outlined text-sm">close</span>
        </button>
      </div>

      <!-- 新建会话 -->
      <div class="px-4 mb-5">
        <button
          @click="handleCreateNewSession"
          class="w-full py-2.5 flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 text-inverse-on-surface rounded-xl text-sm font-semibold transition-all active:scale-[0.98] border border-white/5"
        >
          <span class="material-symbols-outlined text-lg">add</span>
          新建会话
        </button>
      </div>

      <!-- 导航 -->
      <nav class="flex-1 px-3 space-y-0.5 overflow-y-auto">
        <router-link
          to="/chat"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium"
          :class="{
            'bg-white/10 text-inverse-on-surface': $route.path === '/chat',
            'text-inverse-on-surface/50 hover:bg-white/5 hover:text-inverse-on-surface/80': $route.path !== '/chat'
          }"
        >
          <span class="material-symbols-outlined text-lg" :style="{ fontVariationSettings: $route.path === '/chat' ? 'FILL 1' : 'FILL 0' }">chat_bubble</span>
          对话
        </router-link>

        <!-- 会话历史列表 -->
        <div v-if="$route.path === '/chat'" class="mt-3">
          <div class="flex items-center justify-between px-3 mb-1.5">
            <span class="text-[10px] font-bold text-inverse-on-surface/30 uppercase tracking-wider">历史会话</span>
            <button @click="handleCreateNewSession" class="p-1 hover:bg-white/10 rounded-md transition-colors" title="新建会话">
              <span class="material-symbols-outlined text-sm text-inverse-on-surface/40">add</span>
            </button>
          </div>
          <div class="space-y-0.5 max-h-[40vh] overflow-y-auto">
            <div
              v-for="session in store.sessionHistory"
              :key="session.id"
              @click="handleLoadSession(session.id)"
              class="group flex items-start gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
              :class="{
                'bg-white/10': store.currentSessionId === session.id,
                'hover:bg-white/5': store.currentSessionId !== session.id
              }"
            >
              <span class="material-symbols-outlined text-base mt-0.5 shrink-0"
                :class="store.currentSessionId === session.id ? 'text-inverse-on-surface' : 'text-inverse-on-surface/30'"
                :style="{ fontVariationSettings: store.currentSessionId === session.id ? 'FILL 1' : 'FILL 0' }">
                chat
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold truncate" :class="store.currentSessionId === session.id ? 'text-inverse-on-surface' : 'text-inverse-on-surface/60'">
                  {{ getDisplaySessionName(session) }}
                </p>
                <p v-if="shouldShowPreview(session)" class="text-[10px] text-inverse-on-surface/25 truncate mt-0.5">
                  {{ session.last_message_preview }}
                </p>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-[9px] text-inverse-on-surface/25">{{ formatSessionTime(session.updated_at) }}</span>
                  <span v-if="session.message_count" class="text-[9px] text-inverse-on-surface/25">{{ session.message_count }}条</span>
                </div>
              </div>
              <button
                @click.stop="handleDeleteSession(session.id)"
                class="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 rounded-md text-red-400 transition-all"
                title="删除">
                <span class="material-symbols-outlined text-sm">delete</span>
              </button>
            </div>
          </div>
          <div v-if="store.isLoading" class="px-3 py-3 text-center">
            <span class="material-symbols-outlined animate-spin text-sm text-inverse-on-surface/30">progress_activity</span>
          </div>
          <div v-else-if="store.sessionHistory.length === 0 && store.isSessionsLoaded" class="px-3 py-4 text-center text-xs text-inverse-on-surface/25">
            暂无会话
          </div>
        </div>

        <router-link to="/uploads" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium mt-2"
          :class="{
            'bg-white/10 text-inverse-on-surface': $route.path === '/uploads',
            'text-inverse-on-surface/50 hover:bg-white/5 hover:text-inverse-on-surface/80': $route.path !== '/uploads'
          }">
          <span class="material-symbols-outlined text-lg" :style="{ fontVariationSettings: $route.path === '/uploads' ? 'FILL 1' : 'FILL 0' }">database</span>
          知识库
        </router-link>

        <router-link to="/settings" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium"
          :class="{
            'bg-white/10 text-inverse-on-surface': $route.path === '/settings',
            'text-inverse-on-surface/50 hover:bg-white/5 hover:text-inverse-on-surface/80': $route.path !== '/settings'
          }">
          <span class="material-symbols-outlined text-lg" :style="{ fontVariationSettings: $route.path === '/settings' ? 'FILL 1' : 'FILL 0' }">settings</span>
          设置
        </router-link>
      </nav>

      <!-- 退出 -->
      <div class="px-3 pt-3 border-t border-white/5">
        <button @click="handleLogout" class="w-full flex items-center gap-3 px-3 py-2.5 text-inverse-on-surface/40 hover:bg-white/5 hover:text-inverse-on-surface/70 rounded-lg transition-all text-sm font-medium">
          <span class="material-symbols-outlined text-lg">logout</span>
          退出登录
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="min-h-screen transition-all duration-300" :class="isMobile ? 'ml-0' : 'ml-60'">
      <!-- 顶部栏 -->
      <header class="flex justify-between items-center px-5 md:px-8 w-full sticky top-0 z-30 h-14 bg-background/80 backdrop-blur-md border-b border-outline-variant/30">
        <div class="flex items-center gap-4">
          <button v-if="isMobile" @click="sidebarOpen = true" class="p-1.5 hover:bg-surface-container rounded-lg">
            <span class="material-symbols-outlined text-on-surface-variant">menu</span>
          </button>
          <h2 class="text-base md:text-lg font-bold text-on-surface tracking-tight">{{ pageTitle }}</h2>
          <div v-if="$route.path === '/settings'" class="hidden sm:block px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-widest">v2.5</div>
        </div>
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant/50 cursor-pointer hover:text-on-surface-variant transition-colors">notifications</span>
          <span class="material-symbols-outlined text-[18px] text-on-surface-variant/50 cursor-pointer hover:text-on-surface-variant transition-colors">help_outline</span>
        </div>
      </header>

      <!-- 内容 -->
      <div class="flex-1">
        <router-view />
      </div>
    </main>

    <!-- 装饰光晕 -->
    <div class="fixed top-20 right-[-100px] w-[500px] h-[500px] bg-primary/3 rounded-full blur-[120px] pointer-events-none -z-10"></div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from './stores/appStore'
import { authService } from './services/auth'

const router = useRouter()
const store = useAppStore()
const sidebarOpen = ref(false)
const windowWidth = ref(window.innerWidth)

const isMobile = computed(() => windowWidth.value < 768)

const pageTitle = computed(() => {
  if (router.currentRoute.value.path === '/chat') return '对话'
  if (router.currentRoute.value.path === '/uploads') return '知识库'
  if (router.currentRoute.value.path === '/settings') return '设置'
  return 'Ex-Agent'
})

const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) sidebarOpen.value = false
}

function formatSessionTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 获取会话显示名称：如果是"新会话"且有预览内容，则显示预览作为标题
function getDisplaySessionName(session) {
  if (session.session_name === '新会话' && session.last_message_preview) {
    return session.last_message_preview
  }
  return session.session_name || '新会话'
}

// 判断是否应该显示预览小字：当标题不是预览内容时才显示
function shouldShowPreview(session) {
  // 如果标题已经是预览内容，则不显示预览小字
  if (session.session_name === '新会话' && session.last_message_preview) {
    return false
  }
  return session.last_message_preview
}

async function handleLoadSession(sessionId) {
  await store.loadSession(sessionId)
  sidebarOpen.value = false
  if (router.currentRoute.value.path !== '/chat') router.push('/chat')
}

async function handleDeleteSession(sessionId) {
  if (confirm('确定要删除这个会话吗？')) await store.deleteSession(sessionId)
}

function handleCreateNewSession() {
  store.createNewSession()
  sidebarOpen.value = false
  if (router.currentRoute.value.path !== '/chat') router.push('/chat')
}

function handleLogout() {
  authService.logout()
  store.resetState()
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (authService.isAuthenticated() && !store.isInitialized) {
    store.init()
    store.isInitialized = true
  }
})

onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>
