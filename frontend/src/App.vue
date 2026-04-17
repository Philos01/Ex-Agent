<template>
  <div class="min-h-screen bg-surface text-on-surface">
    <!-- 移动端侧边栏遮罩 -->
    <div v-if="sidebarOpen && isMobile" class="fixed inset-0 bg-black/50 z-40" @click="sidebarOpen = false"></div>

    <!-- 侧边栏导航 -->
    <aside 
      class="h-screen bg-[#e6e8ea] flex flex-col p-4 space-y-6 z-50 transition-all duration-300"
      :class="[
        sidebarOpen || !isMobile ? 'translate-x-0' : '-translate-x-full',
        isMobile ? 'fixed left-0 top-0 w-72' : 'w-64 fixed left-0 top-0'
      ]"
    >
      <div class="flex items-center justify-between mb-4 px-2">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-on-primary">
            <span class="material-symbols-outlined">biotech</span>
          </div>
          <div>
            <h1 class="text-lg font-black text-[#006b5f] leading-tight">Ex-Agent</h1>
            <p class="text-[10px] font-semibold tracking-wider text-on-surface-variant opacity-70 uppercase">Precision Lab OS</p>
          </div>
        </div>
        <button v-if="isMobile" @click="sidebarOpen = false" class="p-2 hover:bg-surface-container rounded-lg">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      
      <button 
        @click="handleCreateNewSession" 
        class="w-full py-2.5 px-4 bg-primary text-on-primary rounded-xl font-bold shadow-lg shadow-primary/30 flex items-center justify-center space-x-2 active:scale-95 transition-transform border-2 border-primary/50 hover:bg-primary/90 hover:border-primary"
      >
        <span class="material-symbols-outlined text-lg">add</span>
        <span class="font-manrope text-sm font-semibold tracking-wide">新建会话</span>
      </button>
      
      <nav class="flex-1 space-y-1 overflow-y-auto">
        <router-link 
          to="/chat" 
          class="flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all group"
          :class="{
            'bg-white text-[#006b5f] rounded-lg shadow-sm font-bold': $route.path === '/chat',
            'text-slate-600 hover:bg-[#f2f4f6]': $route.path !== '/chat'
          }"
        >
          <span class="material-symbols-outlined text-lg group-hover:text-primary transition-colors" :style="{ fontVariationSettings: $route.path === '/chat' ? 'FILL 1' : 'FILL 0' }">chat_bubble</span>
          <span class="font-manrope text-sm font-semibold tracking-wide">对话</span>
        </router-link>
        
        <!-- 会话列表 -->
        <div v-if="$route.path === '/chat'" class="mt-4 px-2">
          <div class="flex items-center justify-between mb-2 px-2">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">历史会话</span>
            <button 
              @click="handleCreateNewSession" 
              class="p-1 hover:bg-surface-container rounded-md transition-colors"
              title="新建会话"
            >
              <span class="material-symbols-outlined text-sm">add</span>
            </button>
          </div>
          <div class="space-y-1 max-h-[40vh] overflow-y-auto">
            <div
              v-for="session in store.sessionHistory"
              :key="session.id"
              @click="handleLoadSession(session.id)"
              class="group flex items-start space-x-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
              :class="{
                'bg-white text-[#006b5f] shadow-sm': store.currentSessionId === session.id,
                'text-slate-600 hover:bg-[#f2f4f6]': store.currentSessionId !== session.id
              }"
            >
              <span class="material-symbols-outlined text-lg mt-0.5 shrink-0" :style="{ fontVariationSettings: store.currentSessionId === session.id ? 'FILL 1' : 'FILL 0' }">
                chat
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold truncate">
                  {{ session.session_name }}
                </p>
                <p 
                  v-if="session.last_message_preview" 
                  class="text-[10px] text-slate-400 truncate mt-0.5"
                >
                  {{ session.last_message_preview }}
                </p>
                <div class="flex items-center gap-2 mt-0.5">
                  <span class="text-[9px] text-slate-400">
                    {{ formatSessionTime(session.updated_at) }}
                  </span>
                  <span v-if="session.message_count" class="text-[9px] text-slate-400">
                    {{ session.message_count }} 条消息
                  </span>
                </div>
              </div>
              <button 
                @click.stop="handleDeleteSession(session.id)"
                class="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-50 rounded-md text-red-400 hover:text-red-500 transition-all"
                title="删除会话"
              >
                <span class="material-symbols-outlined text-sm">delete</span>
              </button>
            </div>
          </div>
          <div v-if="store.isLoading" class="px-3 py-2 text-center text-sm text-slate-400">
            <span class="material-symbols-outlined animate-spin text-base">progress_activity</span>
          </div>
          <div v-else-if="store.sessionHistory.length === 0 && store.isSessionsLoaded" class="px-3 py-4 text-center text-sm text-slate-400">
            暂无会话，开始新对话吧！
          </div>
        </div>
        
        <router-link 
          to="/uploads" 
          class="flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all group mt-4"
          :class="{
            'bg-white text-[#006b5f] rounded-lg shadow-sm font-bold': $route.path === '/uploads',
            'text-slate-600 hover:bg-[#f2f4f6]': $route.path !== '/uploads'
          }"
        >
          <span class="material-symbols-outlined text-lg group-hover:text-primary transition-colors" :style="{ fontVariationSettings: $route.path === '/uploads' ? 'FILL 1' : 'FILL 0' }">database</span>
          <span class="font-manrope text-sm font-semibold tracking-wide">知识库</span>
        </router-link>
        
        <router-link 
          to="/settings" 
          class="flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all group"
          :class="{
            'bg-white text-[#006b5f] rounded-lg shadow-sm font-bold': $route.path === '/settings',
            'text-slate-600 hover:bg-[#f2f4f6]': $route.path !== '/settings'
          }"
        >
          <span class="material-symbols-outlined text-lg group-hover:text-primary transition-colors" :style="{ fontVariationSettings: $route.path === '/settings' ? 'FILL 1' : 'FILL 0' }">settings</span>
          <span class="font-manrope text-sm font-semibold tracking-wide">设置</span>
        </router-link>
      </nav>
      
      <div class="pt-4 border-t border-outline-variant/10 space-y-1">
        <button @click="handleLogout" class="w-full flex items-center space-x-3 px-4 py-2.5 text-slate-600 hover:bg-[#f2f4f6] rounded-lg transition-all">
          <span class="material-symbols-outlined text-lg">logout</span>
          <span class="font-manrope text-sm font-semibold tracking-wide">退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main 
      class="min-h-screen transition-all duration-300"
      :class="isMobile ? 'ml-0' : 'ml-64'"
    >
      <!-- 顶部栏 -->
      <header class="flex justify-between items-center px-4 md:px-8 w-full sticky top-0 z-30 h-16 bg-[#f7f9fb] transition-colors duration-200">
        <div class="flex items-center space-x-4">
          <button v-if="isMobile" @click="sidebarOpen = true" class="p-2 hover:bg-surface-container rounded-lg">
            <span class="material-symbols-outlined">menu</span>
          </button>
          <h2 class="font-manrope text-lg md:text-xl font-bold tracking-tighter text-[#006b5f]">
            {{ pageTitle }}
          </h2>
          <template v-if="$route.path === '/settings'">
            <div class="hidden sm:block px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold uppercase tracking-widest">v2.4.0-Stable</div>
          </template>
          <template v-else-if="$route.path === '/uploads'">
            <div class="hidden sm:block h-4 w-px bg-outline-variant opacity-30"></div>
            <div class="hidden sm:flex items-center gap-2 text-on-surface-variant font-medium text-sm tracking-tight">
              <span class="material-symbols-outlined text-base">folder_open</span>
              知识库 / 资产
            </div>
          </template>
          <template v-else-if="$route.path === '/chat'">
            <div class="hidden sm:block h-4 w-px bg-outline-variant/30"></div>
            <span class="hidden sm:inline text-sm font-medium text-on-surface-variant">会话</span>
          </template>
        </div>
        <div class="flex items-center space-x-2 md:space-x-4 text-slate-500">
          <span class="material-symbols-outlined text-[20px]">notifications</span>
          <span class="material-symbols-outlined text-[20px]">help_outline</span>
        </div>
      </header>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-auto">
        <router-view />
      </div>
    </main>

    <!-- 浮动装饰 -->
    <div class="fixed top-20 right-[-100px] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -z-10"></div>
    <div class="fixed bottom-0 left-[-50px] w-[300px] h-[300px] bg-secondary-container/10 rounded-full blur-[100px] pointer-events-none -z-10"></div>
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
  if (router.currentRoute.value.path === '/chat') return 'Ex-Agent'
  if (router.currentRoute.value.path === '/uploads') return 'Ex-Agent'
  if (router.currentRoute.value.path === '/settings') return 'Ex-Agent'
  return ''
})

const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) {
    sidebarOpen.value = false
  }
}

function formatSessionTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

async function handleLoadSession(sessionId) {
  console.log('[DEBUG] Loading session:', sessionId)
  await store.loadSession(sessionId)
  sidebarOpen.value = false
  // 确保路由在/chat
  if (router.currentRoute.value.path !== '/chat') {
    router.push('/chat')
  }
}

async function handleDeleteSession(sessionId) {
  console.log('[DEBUG] Deleting session:', sessionId)
  if (confirm('确定要删除这个会话吗？')) {
    await store.deleteSession(sessionId)
  }
}

function handleCreateNewSession() {
  console.log('[DEBUG] Creating new session...')
  store.createNewSession()
  sidebarOpen.value = false
  // 确保路由在/chat
  if (router.currentRoute.value.path !== '/chat') {
    router.push('/chat')
  }
  console.log('[DEBUG] New session created')
}

function createNewSession() {
  store.createNewSession()
  router.push('/chat')
}

function handleLogout() {
  authService.logout()
  store.resetState()
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 如果用户已登录且 store 未初始化，则初始化
  if (authService.isAuthenticated() && !store.isInitialized) {
    store.init()
    store.isInitialized = true
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>
