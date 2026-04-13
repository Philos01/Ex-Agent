<template>
  <div class="flex-1 flex flex-col h-[calc(100vh-4rem)]">
    <!-- 聊天消息区域 -->
    <div 
      ref="scrollRef" 
      class="flex-1 overflow-y-auto px-4 md:px-12 py-4 md:py-8 chat-scrollbar"
    >
      <!-- 欢迎界面 -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center px-4">
        <div class="w-16 h-16 md:w-20 md:h-20 bg-primary-container rounded-full flex items-center justify-center mb-4 md:mb-6">
          <span class="material-symbols-outlined text-4xl md:text-5xl text-primary">psychology</span>
        </div>
        <h2 class="text-xl md:text-2xl font-bold text-on-surface mb-2 md:mb-3">欢迎使用 Ex-Agent</h2>
        <p class="text-on-surface-variant max-w-md mb-4 md:mb-6 text-sm md:text-base">您的智能通用助手已就绪。上传文档到知识库，然后开始提问吧！</p>
        <div class="flex flex-wrap justify-center gap-2 md:gap-3">
          <button 
            @click="handleSampleQuestion('这个项目的主要功能是什么？')"
            class="px-3 py-2 md:px-4 md:py-2 bg-surface-container-high rounded-xl text-on-surface-variant text-sm font-medium hover:bg-surface-container transition-colors"
          >
            查看示例问题
          </button>
          <button 
            @click="testDataTable"
            class="px-3 py-2 md:px-4 md:py-2 bg-primary-container rounded-xl text-primary text-sm font-medium hover:bg-primary-container/80 transition-colors"
          >
            测试数据表格
          </button>
          <button 
            @click="testDataChart"
            class="px-3 py-2 md:px-4 md:py-2 bg-tertiary-container rounded-xl text-tertiary text-sm font-medium hover:bg-tertiary-container/80 transition-colors"
          >
            测试数据图表
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-else class="max-w-full md:max-w-4xl mx-auto space-y-4 md:space-y-8">
        <div v-for="(m, index) in messages" :key="index" class="flex flex-col">
          <!-- 用户消息 -->
          <div v-if="m.role === 'user'" class="flex flex-col items-end mb-2 md:mb-4">
            <div class="flex items-center gap-2 mb-1 md:mb-2 pr-1 md:pr-2">
              <span class="text-xs text-outline">{{ formatTime(m.time) }}</span>
              <span class="text-xs text-outline">·</span>
              <span class="text-sm font-semibold text-on-surface-variant">用户</span>
            </div>
            <div class="max-w-[90%] md:max-w-2xl bg-primary-container text-white px-4 md:px-6 py-3 md:py-4 rounded-2xl rounded-tr-none shadow-sm">
              <p class="whitespace-pre-wrap text-sm md:text-base">{{ m.text }}</p>
            </div>
          </div>

          <!-- 助手消息 -->
          <div v-else class="flex flex-col">
            <div class="flex items-center gap-2 mb-2 md:mb-3 pl-1 md:pl-2">
              <span class="text-sm font-semibold text-on-surface-variant">Ex-Agent</span>
              <span class="text-xs text-outline">·</span>
              <span class="text-xs text-outline">{{ formatTime(m.time) }}</span>
            </div>
            
            <div class="bg-white rounded-2xl md:rounded-3xl p-4 md:p-8 shadow-sm shadow-on-surface/[0.02] border border-outline-variant/10 max-w-full md:max-w-4xl">
              <div class="flex items-center gap-2 mb-4 md:mb-6">
                <span class="material-symbols-outlined text-primary">auto_awesome</span>
                <span class="font-bold text-primary tracking-tight text-sm md:text-base">LUMINARY 分析报告</span>
              </div>
              
              <!-- 思考步骤组件 -->
              <ThinkingSteps 
                v-if="m.thinkingState"
                :current-state="m.thinkingState"
                class="mb-4 md:mb-6"
              />
              
              <div class="text-on-surface leading-relaxed text-base md:text-[17px] space-y-3 md:space-y-4">
                <div v-if="m.text === '' && index === messages.length - 1 && (loading || streaming) && !m.thinkingState" class="flex items-center gap-2 py-2">
                  <div class="flex gap-1">
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '0ms' }"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '150ms' }"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '300ms' }"></div>
                  </div>
                  <span class="text-on-surface-variant text-sm">正在生成...</span>
                </div>
                <div v-else-if="m.text" v-html="renderMarkdown(m.text)" class="markdown-content"></div>
              </div>

              <!-- 动态组件渲染 -->
              <div v-if="m.components && m.components.length > 0" class="mt-4 md:mt-6 space-y-4">
                <component
                  v-for="(comp, idx) in m.components"
                  :key="idx"
                  :is="getComponent(comp.type)"
                  v-bind="comp.props"
                />
              </div>

              <!-- 引用来源 -->
              <div v-if="m.sources && m.sources.length > 0" class="mt-4 md:mt-8 p-4 md:p-6 bg-surface-container rounded-xl">
                <div class="flex items-center justify-between mb-3 md:mb-4">
                  <h4 class="font-bold text-on-surface text-sm md:text-base">引用来源 ({{ getUniqueSources(m.sources).length }}篇)</h4>
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-bold text-primary/70">按相关性排序</span>
                    <button 
                      v-if="getUniqueSources(m.sources).length > 5"
                      @click="toggleSourcesExpand(m)"
                      class="text-[10px] font-bold text-primary flex items-center gap-1 hover:text-primary/80 transition-colors"
                    >
                      <span class="material-symbols-outlined text-sm">{{ m.sourcesExpanded ? 'expand_less' : 'expand_more' }}</span>
                      {{ m.sourcesExpanded ? '收起' : '展开全部' }}
                    </button>
                  </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-3">
                  <div 
                    v-for="(src, srcIndex) in getDisplaySources(m)" 
                    :key="srcIndex"
                    class="p-3 md:p-4 bg-white rounded-lg border border-outline-variant/10 hover:border-primary/30 transition-all group cursor-pointer relative"
                    @click="openDocumentPreview(src)"
                    @mouseenter="(e) => showHoverSource(e, src)"
                    @mouseleave="hideHoverSource"
                  >
                    <div class="flex items-start gap-2">
                      <span class="material-symbols-outlined text-primary text-lg md:text-xl shrink-0">description</span>
                      <div class="flex-1 min-w-0">
                        <p class="font-semibold text-on-surface text-xs md:text-sm truncate">{{ src.source || src.filename || '文档' }}</p>
                        <p v-if="src.text" class="text-on-surface-variant text-[10px] md:text-xs mt-1 line-clamp-2">{{ src.text }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 mt-2 md:mt-3 px-1 md:px-2">
              <span class="text-[10px] font-bold text-primary/80 uppercase tracking-wide">Ex-Agent</span>
              <span class="text-xs text-outline">·</span>
            </div>
          </div>
        </div>
        <div ref="endRef"></div>
      </div>
    </div>

    <!-- 引用源悬停预览卡片 -->
    <CitationHoverCard
      v-if="hoverSource.visible"
      :visible="hoverSource.visible"
      :source="hoverSource.source"
      :position="hoverSource.position"
    />

    <!-- 文档预览面板 -->
    <DocumentPreviewPanel
      :visible="documentPreview.visible"
      :filename="documentPreview.filename"
      :chunk-index="documentPreview.chunkIndex"
      :source-text="documentPreview.sourceText"
      @close="closeDocumentPreview"
    />

    <!-- 输入区域 -->
    <footer class="px-4 md:px-12 py-4 md:py-8 bg-surface/50 backdrop-blur-md">
      <div class="max-w-full md:max-w-4xl mx-auto relative group">
        <div class="absolute inset-0 bg-primary/5 blur-xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
        <div class="relative flex items-end gap-2 md:gap-4 bg-surface-container-lowest p-2 md:p-3 rounded-xl md:rounded-2xl shadow-lg shadow-on-surface/[0.03] border border-outline-variant/20 focus-within:border-primary/40 transition-all">
          <textarea 
            v-model="q" 
            @keydown="handleKeyDown"
            class="flex-1 bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-outline/60 py-2 md:py-3 resize-none font-medium leading-relaxed text-sm md:text-base"
            placeholder="向 Ex-Agent 咨询..."
            rows="1"
            :disabled="loading || streaming"
          />
          <button 
            @click="sendStream" 
            :disabled="loading || streaming"
            class="h-9 w-9 md:h-10 md:w-10 bg-black text-white rounded-lg md:rounded-xl flex items-center justify-center shadow-lg shadow-black/20 transition-transform active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading || streaming" class="material-symbols-outlined animate-spin text-sm md:text-base">progress_activity</span>
            <span v-else class="material-symbols-outlined text-sm md:text-base">send</span>
          </button>
        </div>
        
        <div class="flex justify-between px-2 md:px-4 mt-2 md:mt-3">
          <div class="flex items-center gap-2 md:gap-4">
            <span class="text-[10px] font-bold text-outline uppercase flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-primary-container rounded-full animate-pulse"></span>
              {{ loading || streaming ? '正在生成...' : 'AI 就绪' }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="showSidebar = !showSidebar"
              class="text-[10px] font-bold text-primary uppercase tracking-tight flex items-center gap-1 hover:text-primary/80 transition-colors"
            >
              <span class="material-symbols-outlined text-sm">tune</span>
              <span class="hidden md:inline">{{ showSidebar ? '隐藏参数' : '参数设置' }}</span>
            </button>
          </div>
        </div>
      </div>
    </footer>

    <!-- 参数设置侧边栏遮罩（所有设备） -->
    <div 
      v-if="showSidebar" 
      class="fixed inset-0 bg-black/20 z-40 transition-opacity duration-300"
      :class="isMobile ? 'bg-black/30' : 'bg-black/10'"
      @click="showSidebar = false"
    ></div>

    <!-- 参数设置侧边栏 -->
    <transition name="slide-in-right">
      <aside v-if="showSidebar" class="fixed right-0 top-16 bottom-0 w-80 md:w-80 bg-surface border-l border-outline-variant/20 overflow-y-auto chat-scrollbar z-50 shadow-2xl">
        <div class="p-4 md:p-6 space-y-6 md:space-y-8">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-on-surface">生成参数</h3>
            <button @click="showSidebar = false" class="p-2 hover:bg-surface-container rounded-lg transition-colors">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <!-- 检索文档数 -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">检索文档数</label>
              <span class="text-2xl font-black text-primary">{{ params.top_k }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.top_k" 
              min="1" 
              max="20"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
          </div>

          <!-- 温度 -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">温度 (Temperature)</label>
              <span class="text-2xl font-black" :class="params.temperature > 1.5 ? 'text-error' : params.temperature > 0.7 ? 'text-tertiary' : 'text-primary'">{{ params.temperature.toFixed(1) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.temperature" 
              min="0" 
              max="2" 
              step="0.1"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
            <p class="text-[11px] text-on-surface-variant leading-relaxed">数值越高，回答越有创意；数值越低，回答越精确和一致</p>
          </div>

          <!-- Top P -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">Top P</label>
              <span class="text-2xl font-black text-primary">{{ params.top_p.toFixed(2) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.top_p" 
              min="0" 
              max="1" 
              step="0.05"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
          </div>

          <!-- 最大令牌数 -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">最大令牌数</label>
              <span class="text-2xl font-black text-primary">{{ params.max_tokens }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.max_tokens" 
              min="256" 
              max="8192" 
              step="256"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
          </div>

          <!-- 存在惩罚 -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">存在惩罚</label>
              <span class="text-2xl font-black" :class="params.presence_penalty > 1 ? 'text-error' : 'text-primary'">{{ params.presence_penalty.toFixed(1) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.presence_penalty" 
              min="-2" 
              max="2" 
              step="0.1"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
          </div>

          <!-- 频率惩罚 -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-sm font-bold text-on-surface">频率惩罚</label>
              <span class="text-2xl font-black" :class="params.frequency_penalty > 1 ? 'text-error' : 'text-primary'">{{ params.frequency_penalty.toFixed(1) }}</span>
            </div>
            <input 
              type="range" 
              v-model.number="params.frequency_penalty" 
              min="-2" 
              max="2" 
              step="0.1"
              @input="updateParams"
              class="w-full h-3 bg-surface-container-high rounded-full appearance-none cursor-pointer border border-outline-variant/50"
            />
          </div>

          <!-- 重置按钮 -->
          <button 
            @click="resetParams"
            class="w-full py-3 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
          >
            重置为默认值
          </button>
        </div>
      </aside>
    </transition>

    <!-- 参数设置开关按钮 - 固定在右侧 -->
    <button 
      v-if="!showSidebar"
      @click="showSidebar = true"
      class="fixed right-2 md:right-4 bottom-20 md:top-1/2 md:-translate-y-1/2 z-50 
             w-10 h-10 md:w-12 md:h-12 
             flex items-center justify-center
             bg-primary text-on-primary border-none rounded-xl shadow-lg 
             hover:bg-primary/90 transition-all duration-300"
    >
      <!-- 稍微调整图标大小以适配容器 -->
      <span class="material-symbols-outlined text-2xl md:text-3xl">settings</span>
    </button>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed, watch } from 'vue'
import { useAppStore } from '../stores/appStore'
import { useRoute } from 'vue-router'
import api from '../services/api'
import { sessionService } from '../services/sessions'
import ThinkingSteps from '../components/gen-ui/ThinkingSteps.vue'
import CitationHoverCard from '../components/gen-ui/CitationHoverCard.vue'
import DocumentPreviewPanel from '../components/gen-ui/DocumentPreviewPanel.vue'
import { getComponent } from '../components/gen-ui/ComponentRegistry.js'
import { marked } from 'marked'

const store = useAppStore()
const route = useRoute()

// 安全的时间格式化函数 - 修复时区问题
const formatTime = (timeValue) => {
  if (!timeValue) {
    return '--:--'
  }
  // 如果已经是格式化的时间字符串，直接返回
  if (typeof timeValue === 'string' && timeValue.includes(':') && !timeValue.includes('T')) {
    return timeValue
  }
  try {
    let date
    if (typeof timeValue === 'string') {
      // 处理 ISO 格式字符串，避免时区偏移
      if (timeValue.includes('T')) {
        // 对于 ISO 格式，直接提取本地时间
        // 例如：2024-04-11T18:30:00 -> 直接取 18:30
        const timePart = timeValue.split('T')[1]
        if (timePart) {
          const hourMinute = timePart.split(':').slice(0, 2).join(':')
          if (hourMinute) {
            return hourMinute
          }
        }
      }
      // 如果以上方法不行，尝试正常解析
      date = new Date(timeValue)
    } else if (timeValue instanceof Date) {
      date = timeValue
    }
    
    if (date && !isNaN(date.getTime())) {
      // 使用本地时区格式化
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${hours}:${minutes}`
    }
  } catch (e) {
    console.error('[DEBUG] Failed to format time:', timeValue, e)
  }
  return '--:--'
}

const q = ref('')
const messages = ref([...store.chatMessages])
const loading = ref(false)
const streaming = ref(false)
const showSidebar = ref(false)
const params = ref({ ...store.chatParams })
const endRef = ref(null)
const scrollRef = ref(null)
const windowWidth = ref(window.innerWidth)
const savingMessage = ref(false)

// 引用源悬停预览状态
const hoverSource = ref({
  visible: false,
  source: null,
  position: { x: 0, y: 0 }
})

// 文档预览面板状态
const documentPreview = ref({
  visible: false,
  filename: null,
  chunkIndex: null
})

const isMobile = computed(() => windowWidth.value < 768)

// 计算属性：将Markdown转换为HTML
const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text, {
    breaks: true,
    gfm: true
  })
}

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

// 重置界面状态的函数
const resetUI = () => {
  q.value = ''
  loading.value = false
  streaming.value = false
  console.log('[DEBUG] UI reset complete')
}

// 监听store中chatMessages的变化，同步到本地
watch(() => store.chatMessages, (newMessages) => {
  console.log('[DEBUG] store.chatMessages changed:', newMessages.length, 'messages')
  messages.value = [...newMessages]
  // 如果是空数组，说明是新建会话，重置UI
  if (newMessages.length === 0) {
    resetUI()
  }
}, { deep: true })

// 监听路由变化，确保在/chat页面时正确初始化
watch(() => route.path, (newPath) => {
  if (newPath === '/chat') {
    console.log('[DEBUG] Route changed to /chat, syncing messages')
    messages.value = [...store.chatMessages]
    resetUI()
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 组件挂载时确保从store同步消息
  messages.value = [...store.chatMessages]
  console.log('[DEBUG] ChatView mounted, messages:', messages.value.length)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 移除异步操作，避免组件卸载后仍在执行
  console.log('[DEBUG] ChatView unmounted')
})

const scrollToBottom = () => {
  nextTick(() => {
    if (endRef.value) {
      endRef.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const updateParams = () => {
  store.updateChatParams(params.value)
}

const resetParams = () => {
  params.value = {
    top_k: 5,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  }
  updateParams()
}

const handleSampleQuestion = (question) => {
  q.value = question
  sendStream()
}

// 测试数据表格
const testDataTable = () => {
  const userMsg = '测试数据表格'
  const userMessage = { 
    id: `temp_${Date.now()}`,
    role: 'user', 
    text: userMsg, 
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) 
  }
  messages.value.push(userMessage)

  const assistantMessage = { 
    id: `temp_${Date.now() + 1}`,
    role: 'assistant', 
    text: '这是一个测试数据表格，展示不同催化剂的性能对比：', 
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    sources: [],
    thinkingState: null,
    components: [
      {
        type: 'DataTable',
        props: {
          columns: ['催化剂', '产率', '反应温度', '反应时间', '溶剂'],
          data: [
            ['Pd/C', '92%', '80°C', '4h', '乙醇'],
            ['Pt/C', '85%', '90°C', '6h', '甲醇'],
            ['Ru/C', '78%', '75°C', '5h', '异丙醇'],
            ['Rh/C', '88%', '85°C', '3h', '甲苯'],
            ['Ir/C', '95%', '70°C', '8h', '二氯甲烷']
          ]
        }
      }
    ]
  }
  messages.value.push(assistantMessage)
}

// 测试数据图表
const testDataChart = () => {
  const userMsg = '测试数据图表'
  const userMessage = { 
    id: `temp_${Date.now()}`,
    role: 'user', 
    text: userMsg, 
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) 
  }
  messages.value.push(userMessage)

  const assistantMessage = { 
    id: `temp_${Date.now() + 1}`,
    role: 'assistant', 
    text: '这是一个测试数据图表，展示不同温度下的产率变化：', 
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    sources: [],
    thinkingState: null,
    components: [
      {
        type: 'DataChart',
        props: {
          labels: ['60°C', '70°C', '80°C', '90°C', '100°C'],
          values: [65, 78, 92, 85, 70],
          type: 'bar',
          title: '温度对产率的影响'
        }
      }
    ]
  }
  messages.value.push(assistantMessage)
}

const getUniqueSources = (sources) => {
  const seen = new Set()
  return sources.filter(s => {
    const key = s.source || s.filename
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// 获取要显示的来源（支持展开/收起）
const getDisplaySources = (message) => {
  const unique = getUniqueSources(message.sources)
  if (message.sourcesExpanded || unique.length <= 5) {
    return unique
  }
  return unique.slice(0, 5)
}

// 切换来源展开状态
const toggleSourcesExpand = (message) => {
  message.sourcesExpanded = !message.sourcesExpanded
}

// 显示引用源悬停预览
const showHoverSource = (event, source) => {
  const rect = event.target.getBoundingClientRect()
  hoverSource.value = {
    visible: true,
    source: source,
    position: {
      x: rect.left,
      y: rect.bottom + window.scrollY
    }
  }
}

// 隐藏引用源悬停预览
const hideHoverSource = () => {
  hoverSource.value.visible = false
}

// 打开文档预览面板
const openDocumentPreview = (source) => {
  const filename = source.source || source.filename
  const chunkIndex = source.chunk_index !== undefined ? source.chunk_index : null
  const sourceText = source.text || null
  
  documentPreview.value = {
    visible: true,
    filename: filename,
    chunkIndex: chunkIndex,
    sourceText: sourceText
  }
}

// 关闭文档预览面板
const closeDocumentPreview = () => {
  documentPreview.value.visible = false
  documentPreview.value.filename = null
  documentPreview.value.chunkIndex = null
}

// 预览来源（保留向后兼容）
const previewSource = (source) => {
  openDocumentPreview(source)
}

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendStream()
  }
}

const sendStream = async () => {
  if (!q.value.trim() || loading.value || streaming.value) return
  
  const userMsg = q.value.trim()
  q.value = ''
  
  // 确保有活动会话，如果没有则创建
  if (!store.currentSessionId) {
    console.log('[DEBUG] No active session, creating new one...')
    await store.createNewSession()
  }
  
  // 创建临时ID，避免重复保存
  const tempUserId = Date.now() + Math.random()
  const userMessage = { 
    id: `temp_${tempUserId}`,
    role: 'user', 
    text: userMsg, 
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) 
  }
  messages.value.push(userMessage)
  
  // 保存用户消息到数据库
  const savedUserMessage = await saveMessageToDatabase('user', userMsg, null)
  if (savedUserMessage) {
    userMessage.id = savedUserMessage.id
  }
  
  const tempAssistantId = Date.now() + Math.random() + 1
  const assistantMessage = { 
    id: `temp_${tempAssistantId}`,
    role: 'assistant', 
    text: '', 
    time: '正在生成...', 
    sources: [],
    thinkingState: null,
    components: []
  }
  messages.value.push(assistantMessage)
  
  loading.value = true
  streaming.value = true
  scrollToBottom()
  
  try {
    // 准备对话历史（不包含当前刚添加的用户消息和空助手消息）
    const historyMessages = []
    for (let i = 0; i < messages.value.length - 2; i++) {
      const msg = messages.value[i]
      historyMessages.push({
        role: msg.role,
        content: msg.text
      })
    }
    
    console.log('[DEBUG] Sending request with params:', {
      question: userMsg.substring(0, 50) + '...',
      top_k: params.value.top_k,
      temperature: params.value.temperature,
      top_p: params.value.top_p,
      max_tokens: params.value.max_tokens,
      presence_penalty: params.value.presence_penalty,
      frequency_penalty: params.value.frequency_penalty,
      history_count: historyMessages.length
    })
    
    // Use fetch instead of axios for streaming responses
    const response = await fetch('/api/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: userMsg,
        top_k: params.value.top_k,
        temperature: params.value.temperature,
        top_p: params.value.top_p,
        max_tokens: params.value.max_tokens,
        presence_penalty: params.value.presence_penalty,
        frequency_penalty: params.value.frequency_penalty,
        messages: historyMessages
      })
    })
    
    if (!response.ok) throw new Error('API Error')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let sources = []
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'content') {
              fullText += parsed.content
              const lastIndex = messages.value.length - 1
              messages.value[lastIndex].text = fullText
              messages.value[lastIndex].time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
              scrollToBottom()
            } else if (parsed.type === 'sources') {
              sources = parsed.sources || []
              const lastIndex = messages.value.length - 1
              messages.value[lastIndex].sources = sources
            } else if (parsed.type === 'state') {
              const lastIndex = messages.value.length - 1
              messages.value[lastIndex].thinkingState = {
                phase: parsed.phase,
                message: parsed.message,
                progress: parsed.progress
              }
              scrollToBottom()
            } else if (parsed.type === 'component') {
              const lastIndex = messages.value.length - 1
              messages.value[lastIndex].components = messages.value[lastIndex].components || []
              messages.value[lastIndex].components.push({
                type: parsed.component,
                props: parsed.props
              })
              scrollToBottom()
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }
    
    // 保存助手消息到数据库
    if (fullText) {
      const savedAssistantMessage = await saveMessageToDatabase('assistant', fullText, sources)
      if (savedAssistantMessage) {
        const lastIndex = messages.value.length - 1
        messages.value[lastIndex].id = savedAssistantMessage.id
      }
    }
    
  } catch (error) {
    console.error('Error:', error)
    const lastIndex = messages.value.length - 1
    messages.value[lastIndex].text = '抱歉，发生了错误。请检查网络连接或稍后重试。'
  } finally {
    loading.value = false
    streaming.value = false
    store.updateChatMessages(messages.value)
  }
}

// 保存消息到数据库的辅助函数
async function saveMessageToDatabase(role, content, sources) {
  if (!store.currentSessionId) {
    console.warn('[WARN] No session ID available, cannot save message')
    return null
  }
  
  // 确保内容不为空
  if (!content || content.trim() === '') {
    console.warn('[WARN] Cannot save empty message')
    return null
  }
  
  try {
    savingMessage.value = true
    console.log('[DEBUG] Saving message to database:', { role, content: content.substring(0, 50) + '...' })
    const savedMessage = await sessionService.addMessage(store.currentSessionId, role, content, sources)
    // 重新加载会话列表以更新预览
    await store.loadSessionsFromDatabase()
    console.log('[DEBUG] Message saved to database:', savedMessage)
    return savedMessage
  } catch (error) {
    console.error('[ERROR] Failed to save message to database:', error)
    return null
  } finally {
    savingMessage.value = false
  }
}
</script>

<style scoped>
/* 弹跳动画 */
@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* 原slide动画保持兼容 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* 新的增强版滑入动画 */
.slide-in-right-enter-active,
.slide-in-right-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-in-right-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-in-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.slide-in-right-enter-to,
.slide-in-right-leave-from {
  transform: translateX(0);
  opacity: 1;
}

/* 遮罩层淡入淡出 */
.slide-in-right-enter-active + div,
.slide-in-right-leave-active + div {
  transition: opacity 0.3s ease;
}

/* Markdown 内容样式 */
:deep(.markdown-content) {
  line-height: 1.8;
}

:deep(.markdown-content h1) {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1f2937;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

:deep(.markdown-content h2) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #374151;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.markdown-content h3) {
  font-size: 1.25rem;
  font-weight: 600;
  color: #4b5563;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
  font-size: 1.125rem;
  font-weight: 600;
  color: #6b7280;
  margin-top: 0.875rem;
  margin-bottom: 0.375rem;
}

:deep(.markdown-content p) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  color: #374151;
}

:deep(.markdown-content strong) {
  font-weight: 700;
  color: #111827;
}

:deep(.markdown-content em) {
  font-style: italic;
  color: #4b5563;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 1.5rem;
}

:deep(.markdown-content ul) {
  list-style-type: disc;
}

:deep(.markdown-content ol) {
  list-style-type: decimal;
}

:deep(.markdown-content li) {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
  color: #374151;
}

:deep(.markdown-content ul li::marker),
:deep(.markdown-content ol li::marker) {
  color: #3b82f6;
  font-weight: 600;
}

:deep(.markdown-content code) {
  background-color: #f3f4f6;
  color: #dc2626;
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
}

:deep(.markdown-content pre) {
  background-color: #1f2937;
  color: #e5e7eb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-content pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
  font-size: 0.875rem;
  line-height: 1.6;
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  color: #6b7280;
  font-style: italic;
  background-color: #eff6ff;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  padding-right: 0.75rem;
  border-radius: 0 0.375rem 0.375rem 0;
}

:deep(.markdown-content a) {
  color: #3b82f6;
  text-decoration: underline;
  text-underline-offset: 2px;
}

:deep(.markdown-content a:hover) {
  color: #1d4ed8;
}

:deep(.markdown-content table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-content th),
:deep(.markdown-content td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

:deep(.markdown-content th) {
  background-color: #f9fafb;
  font-weight: 600;
  color: #374151;
}

:deep(.markdown-content tr:nth-child(even)) {
  background-color: #f9fafb;
}

:deep(.markdown-content tr:hover) {
  background-color: #f3f4f6;
}

:deep(.markdown-content hr) {
  border: none;
  height: 1px;
  background-color: #e5e7eb;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}

:deep(.markdown-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}
</style>
