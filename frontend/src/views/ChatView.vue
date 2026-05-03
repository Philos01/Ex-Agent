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
        <div v-for="(m, index) in messages" :key="m.id || `msg-${index}`" class="flex flex-col">
          <!-- 用户消息 -->
          <div v-if="m.role === 'user'" class="flex flex-col items-end mb-2 md:mb-4">
            <div class="flex items-center gap-2 mb-1 md:mb-2 pr-1 md:pr-2">
              <span class="text-xs text-outline">{{ formatTime(m.time) }}</span>
              <span class="text-xs text-outline">·</span>
              <span class="text-sm font-semibold text-on-surface-variant">用户</span>
            </div>
            <div class="max-w-[90%] md:max-w-2xl bg-surface-container-high px-4 md:px-6 py-3 md:py-4 rounded-2xl rounded-tr-none shadow-card relative group">
              <p class="whitespace-pre-wrap text-sm md:text-base text-on-surface user-select-text">{{ m.text }}</p>
            </div>
            <button
              @click="copyMessage(m.text)"
              class="copy-btn mt-1 mr-1 w-7 h-7 bg-surface-container rounded-full flex items-center justify-center opacity-60 hover:opacity-100 hover:bg-surface-container-high transition-all"
              :title="'复制消息'"
            >
              <span class="material-symbols-outlined text-[14px] text-on-surface-variant">content_copy</span>
            </button>
          </div>

          <!-- 助手消息 -->
          <div v-else class="flex flex-col">
            <div class="flex items-center gap-2 mb-2 md:mb-3 pl-1 md:pl-2">
              <span class="text-sm font-semibold text-on-surface-variant">Ex-Agent</span>
              <span class="text-xs text-outline">·</span>
              <span class="text-xs text-outline">{{ formatTime(m.time) }}</span>
            </div>
            
            <div class="bg-surface rounded-2xl md:rounded-3xl p-5 md:p-7 shadow-card max-w-full md:max-w-4xl">
              
              <!-- DeepSeek 思考预览 (非ReAct模式或ReAct模式但无reactSteps时独立显示) -->
              <DeepSeekThinkingPreview
                v-if="m.reasoningText && !m.reactSteps"
                :thinking-text="m.reasoningText"
                :is-streaming="index === messages.length - 1 && (loading || streaming || isReActRunning)"
                class="mb-4 md:mb-6"
              />
              
              <!-- ReAct 思考过程展示组件 -->
              <ReActThinkingDisplay 
                v-if="m.reactSteps && m.reactSteps.length > 0"
                :steps="m.reactSteps"
                :is-running="index === messages.length - 1 && isReActRunning && params.use_react"
                class="mb-4 md:mb-6"
              />
              
              <div class="text-on-surface leading-relaxed text-base md:text-[17px] space-y-3 md:space-y-4">
                <!-- 加载动画：文字为空且正在处理中，持续显示直到有内容 -->
                <div v-if="m.text === '' && index === messages.length - 1 && (loading || streaming)" class="flex items-center gap-2 py-2">
                  <div class="flex gap-1">
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '0ms' }"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '150ms' }"></div>
                    <div class="w-2 h-2 bg-primary rounded-full animate-bounce" :style="{ animationDelay: '300ms' }"></div>
                  </div>
                  <span class="text-on-surface-variant text-sm">
                    {{ m.thinkingState?.message || '正在生成...' }}
                  </span>
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
              <button
                @click="copyMessage(m.text)"
                class="copy-btn w-7 h-7 bg-surface-container rounded-full flex items-center justify-center opacity-60 hover:opacity-100 hover:bg-surface-container-high transition-all"
                :title="'复制消息'"
              >
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant">content_copy</span>
              </button>
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
          
          <ModeSelector
            :enable-thinking="params.enable_thinking"
            :reasoning-effort="params.reasoning_effort"
            :use-react="params.use_react"
            :use-graph="params.use_graph"
            :disabled="loading || streaming"
            @update:enable-thinking="handleThinkingUpdate"
            @update:reasoning-effort="handleEffortUpdate"
            @update:use-react="handleReActUpdate"
            @update:use-graph="handleGraphUpdate"
            @show-react-prompt="handleReActPromptFromModeSelector"
          />
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
            class="h-9 w-9 md:h-10 md:w-10 bg-primary text-on-primary rounded-xl flex items-center justify-center shadow-md shadow-primary/20 transition-all active:scale-90 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90"
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

          <!-- 思考模式状态 -->
          <div class="p-4 bg-surface-container rounded-xl space-y-3">
            <h4 class="text-sm font-bold text-on-surface mb-3">思考模式状态</h4>
            <div class="flex items-center justify-between">
              <span class="text-xs text-on-surface-variant">模式状态</span>
              <span 
                class="px-3 py-1 rounded-full text-xs font-bold"
                :class="params.enable_thinking ? 'bg-primary/10 text-primary' : 'bg-surface-container-high text-on-surface-variant'"
              >
                {{ params.enable_thinking ? '已启用' : '已禁用' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-on-surface-variant">思考强度</span>
              <span 
                class="px-3 py-1 rounded-full text-xs font-bold"
                :class="{
                  'bg-error/10 text-error': params.reasoning_effort === 'max',
                  'bg-primary/10 text-primary': params.reasoning_effort === 'high',
                  'bg-tertiary/10 text-tertiary': params.reasoning_effort === 'medium',
                  'bg-surface-container-high text-on-surface-variant': params.reasoning_effort === 'low'
                }"
              >
                {{ params.reasoning_effort ? params.reasoning_effort.toUpperCase() : 'HIGH' }}
              </span>
            </div>
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
    
    <!-- ReAct 模式提示组件 -->
    <ReActModePrompt 
      :visible="showReActPrompt"
      @close="showReActPrompt = false"
      ref="promptRef"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed, watch } from 'vue'
import { useAppStore } from '../stores/appStore'
import { useRoute } from 'vue-router'
import api from '../services/api'
import { sessionService } from '../services/sessions'
import CitationHoverCard from '../components/gen-ui/CitationHoverCard.vue'
import DocumentPreviewPanel from '../components/gen-ui/DocumentPreviewPanel.vue'
import ReActModePrompt from '../components/gen-ui/ReActModePrompt.vue'
import ReActThinkingDisplay from '../components/gen-ui/ReActThinkingDisplay.vue'
import DeepSeekThinkingPreview from '../components/gen-ui/DeepSeekThinkingPreview.vue'
import ModeSelector from '../components/gen-ui/ModeSelector.vue'
import { getComponent } from '../components/gen-ui/ComponentRegistry.js'
import { marked } from 'marked'

const store = useAppStore()
const route = useRoute()

// 安全的时间格式化函数 - 统一使用北京时间
const formatTime = (timeValue) => {
  if (!timeValue) {
    return '--:--'
  }
  // 如果已经是格式化的时间字符串，直接返回
  if (typeof timeValue === 'string' && timeValue.includes(':') && !timeValue.includes('T')) {
    return timeValue
  }
  try {
    const date = new Date(timeValue)
    if (date && !isNaN(date.getTime())) {
      // 转换为北京时间
      const beijingDate = new Date(date.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
      const hours = beijingDate.getHours().toString().padStart(2, '0')
      const minutes = beijingDate.getMinutes().toString().padStart(2, '0')
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
const params = ref({ ...store.chatParams, use_react: false, use_graph: true, reasoning_effort: store.chatParams.reasoning_effort || 'high' })
const endRef = ref(null)
const scrollRef = ref(null)
const windowWidth = ref(window.innerWidth)
const savingMessage = ref(false)

// ReAct 模式相关状态
const showReActPrompt = ref(false)
const reactSteps = ref([])
const isReActRunning = ref(false)
const promptRef = ref(null)

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

// 标志位，防止watcher循环触发
const isSyncingWithStore = ref(false)

// 监听store中chatMessages的变化，同步到本地
watch(() => store.chatMessages, (newMessages) => {
  if (isSyncingWithStore.value) return
  isSyncingWithStore.value = true
  console.log('[DEBUG] store.chatMessages changed:', newMessages.length, 'messages')
  
  // 保存本地的 thinkingState（按消息ID）
  const localThinkingStates = {}
  messages.value.forEach(msg => {
    if (msg.thinkingState) {
      localThinkingStates[msg.id] = msg.thinkingState
    }
  })
  
  // 完全替换为新的消息列表，但保留匹配的 thinkingState
  messages.value = newMessages.map(storeMsg => {
    if (localThinkingStates[storeMsg.id]) {
      return { ...storeMsg, thinkingState: localThinkingStates[storeMsg.id] }
    }
    return storeMsg
  })
  
  // 当切换会话时，重置全局 ReAct 状态！防止之前会话的状态残留！
  reactSteps.value = []
  isReActRunning.value = false
  
  // 如果是空数组，说明是新建会话或切换到了空会话，重置UI
  if (newMessages.length === 0) {
    resetUI()
  }
  
  nextTick(() => {
    isSyncingWithStore.value = false
  })
}, { deep: true })

// 监听messages变化，同步thinkingState到store
watch(messages, (newMessages) => {
  if (isSyncingWithStore.value) return
  isSyncingWithStore.value = true
  
  // 只在本地消息和store消息数量/顺序一致时，尝试同步 thinkingState
  // 避免在添加新消息时覆盖 store
  if (newMessages.length === store.chatMessages.length) {
    // 检查是否有变化的 thinkingState，且消息ID匹配
    let hasThinkingStateChange = false
    const updatedMessages = store.chatMessages.map((storeMsg) => {
      const localMsg = newMessages.find(m => m.id === storeMsg.id)
      if (localMsg && localMsg.thinkingState && localMsg.thinkingState !== storeMsg.thinkingState) {
        hasThinkingStateChange = true
        return { ...storeMsg, thinkingState: localMsg.thinkingState }
      }
      return storeMsg
    })
    if (hasThinkingStateChange) {
      store.updateChatMessages(updatedMessages)
    }
  }
  
  nextTick(() => {
    isSyncingWithStore.value = false
  })
}, { deep: true })

// 监听路由变化，确保在/chat页面时正确初始化
watch(() => route.path, (newPath) => {
  if (newPath === '/chat') {
    console.log('[DEBUG] Route changed to /chat, syncing messages')
    // 保留本地的 thinkingState
    const currentThinkingStates = {}
    messages.value.forEach(msg => {
      if (msg.thinkingState) {
        currentThinkingStates[msg.id] = msg.thinkingState
      }
    })
    messages.value = [...store.chatMessages].map(msg => {
      if (currentThinkingStates[msg.id]) {
        return { ...msg, thinkingState: currentThinkingStates[msg.id] }
      }
      return msg
    })
    resetUI()
  }
})

// 处理窗口可见性变化，确保 thinkingState 和 reasoningText 在切换窗口后不丢失
const handleVisibilityChange = () => {
  // 如果正在流式传输/加载中，不要强制同步，避免覆盖正在生成的内容！
  if (document.visibilityState === 'visible' && !loading.value && !streaming.value && !isReActRunning.value) {
    console.log('[DEBUG] Window became visible, syncing messages with thinkingState and reasoningText')
    // 窗口重新可见时，同步消息并保留 thinkingState 和 reasoningText
    const localThinkingStates = {}
    const localReasoningTexts = {}
    messages.value.forEach(msg => {
      if (msg.thinkingState) {
        localThinkingStates[msg.id] = msg.thinkingState
      }
      if (msg.reasoningText) {
        localReasoningTexts[msg.id] = msg.reasoningText
      }
    })
    messages.value = [...store.chatMessages].map(msg => {
      if (localThinkingStates[msg.id]) {
        msg.thinkingState = localThinkingStates[msg.id]
      }
      if (localReasoningTexts[msg.id]) {
        msg.reasoningText = localReasoningTexts[msg.id]
      }
      return msg
    })
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  // 组件挂载时确保从store同步消息，同时保留本地的 thinkingState 和 reasoningText
  const localThinkingStates = {}
  const localReasoningTexts = {}
  messages.value.forEach(msg => {
    if (msg.thinkingState) {
      localThinkingStates[msg.id] = msg.thinkingState
    }
    if (msg.reasoningText) {
      localReasoningTexts[msg.id] = msg.reasoningText
    }
  })
  messages.value = [...store.chatMessages].map(msg => {
    if (localThinkingStates[msg.id]) {
      msg.thinkingState = localThinkingStates[msg.id]
    }
    if (localReasoningTexts[msg.id]) {
      msg.reasoningText = localReasoningTexts[msg.id]
    }
    return msg
  })
  console.log('[DEBUG] ChatView mounted, messages:', messages.value.length)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
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
    frequency_penalty: 0.0,
    enable_thinking: false,
    use_react: false,
    reasoning_effort: 'high'
  }
  updateParams()
}

const handleReActPromptFromModeSelector = () => {
  // 检查是否应该显示提示（尊重用户的"不再显示"选择）
  if (shouldShowReActPrompt()) {
    showReActPrompt.value = true
  }
}

// 统一的 ReAct 提示显示判断函数
const shouldShowReActPrompt = () => {
  if (!promptRef.value) return true
  return promptRef.value.checkShouldShow()
}

// ModeSelector 组件的事件处理函数
const handleThinkingUpdate = (value) => {
  params.value.enable_thinking = value
  updateParams()
}

const handleEffortUpdate = (value) => {
  params.value.reasoning_effort = value
  updateParams()
}

const handleReActUpdate = (value) => {
  params.value.use_react = value
  updateParams()
}

const handleGraphUpdate = (value) => {
  params.value.use_graph = value
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

// 复制消息文本到剪贴板
const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    // 可以添加一个短暂的提示反馈
    console.log('[DEBUG] Message copied to clipboard')
  } catch (err) {
    console.error('[ERROR] Failed to copy message:', err)
  }
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
    reasoningText: null,
    reactSteps: null,
    components: []
  }
  messages.value.push(assistantMessage)
  
  loading.value = true
  streaming.value = true
  scrollToBottom()
  
  // 初始化 ReAct 状态
  reactSteps.value = []
  isReActRunning.value = params.value.use_react
  
  try {
    // 准备对话历史（不包含当前刚添加的用户消息和空助手消息）
    const historyMessages = []
    for (let i = 0; i < messages.value.length - 2; i++) {
      const msg = messages.value[i]
      const historyMsg = {
        role: msg.role,
        content: msg.text
      }

      // 如果是助手消息且在 ReAct 模式下有工具调用，保留 reasoning_content
      if (msg.role === 'assistant' && msg.reactSteps && msg.reactSteps.length > 0) {
        historyMsg.had_tool_calls = true
        historyMsg.reasoning_content = msg.reasoningText || ''
      } else if (msg.role === 'assistant' && msg.reasoningText) {
        // 非工具调用但有 reasoning_text，标记为无工具调用
        historyMsg.had_tool_calls = false
        // 不传递 reasoning_content，后端会过滤
      }

      historyMessages.push(historyMsg)
    }
    
    console.log('[DEBUG] Sending request with params:', {
      question: userMsg.substring(0, 50) + '...',
      top_k: params.value.top_k,
      temperature: params.value.temperature,
      top_p: params.value.top_p,
      max_tokens: params.value.max_tokens,
      presence_penalty: params.value.presence_penalty,
      frequency_penalty: params.value.frequency_penalty,
      enable_thinking: params.value.enable_thinking,
      use_react: params.value.use_react,
      use_graph: params.value.use_graph,
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
        enable_thinking: params.value.enable_thinking,
        reasoning_effort: params.value.reasoning_effort,
        use_react: params.value.use_react,
        use_graph: params.value.use_graph,
        messages: historyMessages
      })
    })
    
    if (!response.ok) throw new Error('API Error')
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let sources = []
    let receivedFinalAnswer = false  // 防止答案重复
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      // 使用SSE标准的\n\n分隔符
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(data)
            const lastIndex = messages.value.length - 1
            
            if (parsed.type === 'content') {
              if (!receivedFinalAnswer) {  // 如果还没有收到最终答案，才追加内容
                fullText += parsed.content
                messages.value[lastIndex].text = fullText
                messages.value[lastIndex].time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
                scrollToBottom()
              }
            } else if (parsed.type === 'sources') {
              sources = parsed.sources || []
              messages.value[lastIndex].sources = sources
            } else if (parsed.type === 'graph_sources') {
              const existing = sources || []
              const graphNew = parsed.sources || []
              sources = [...existing, ...graphNew]
              messages.value[lastIndex].sources = sources
            } else if (parsed.type === 'state') {
              messages.value[lastIndex].thinkingState = {
                phase: parsed.phase,
                message: parsed.message,
                progress: parsed.progress
              }
              scrollToBottom()
            } else if (parsed.type === 'component') {
              messages.value[lastIndex].components = messages.value[lastIndex].components || []
              messages.value[lastIndex].components.push({
                type: parsed.component,
                props: parsed.props
              })
              scrollToBottom()
            } else if (parsed.type === 'reasoning_chunk' || parsed.type === 'react_reasoning_chunk') {
              if (!messages.value[lastIndex].reasoningText) {
                messages.value[lastIndex].reasoningText = ''
              }
              messages.value[lastIndex].reasoningText += parsed.content
              scrollToBottom()
            } else if (parsed.type === 'react_thought') {
              reactSteps.value.push({
                type: 'thought',
                content: parsed.content,
                reasoning: messages.value[lastIndex].reasoningText || '',
                timestamp: Date.now()
              })
              // Clear reasoning accumulator for next iteration
              messages.value[lastIndex].reasoningText = ''
              messages.value[lastIndex].reactSteps = [...reactSteps.value]
              scrollToBottom()
            } else if (parsed.type === 'react_action') {
              console.log('[DEBUG] Received react_action event:', parsed)
              console.log('[DEBUG] react_action input type:', typeof parsed.input)
              console.log('[DEBUG] react_action input:', parsed.input)
              // 确保 input 是正确的格式
              let actionInput = parsed.input
              if (typeof actionInput === 'string') {
                try {
                  actionInput = JSON.parse(actionInput)
                } catch (e) {
                  console.log('[DEBUG] Failed to parse action input as JSON:', e)
                }
              }
              console.log('[DEBUG] Processed action input:', actionInput, 'type:', typeof actionInput)
              reactSteps.value.push({
                type: 'action',
                name: parsed.name,
                input: actionInput,
                timestamp: Date.now()
              })
              messages.value[lastIndex].reactSteps = [...reactSteps.value]
              scrollToBottom()
            } else if (parsed.type === 'react_observation') {
              reactSteps.value.push({
                type: 'observation',
                content: parsed.content,
                timestamp: Date.now()
              })
              messages.value[lastIndex].reactSteps = [...reactSteps.value]
              scrollToBottom()
            } else if (parsed.type === 'react_final_answer') {
              console.log('[DEBUG] Received react_final_answer event:', parsed)
              receivedFinalAnswer = true  // 设置标志，防止后续重复追加
              const finalAnswerContent = parsed.content
              reactSteps.value.push({
                type: 'final_answer',
                content: finalAnswerContent,
                timestamp: Date.now()
              })
              messages.value[lastIndex].reactSteps = [...reactSteps.value]
              // 同时更新 fullText 和消息文本
              fullText = finalAnswerContent
              messages.value[lastIndex].text = fullText
              messages.value[lastIndex].time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
              // 确保所有状态正确更新
              console.log('[DEBUG] Setting states to false: isReActRunning, loading, streaming')
              isReActRunning.value = false
              loading.value = false
              streaming.value = false
              console.log('[DEBUG] States after reset:', {
                isReActRunning: isReActRunning.value,
                loading: loading.value,
                streaming: streaming.value,
                messageText: messages.value[lastIndex].text
              })
              // 使用 nextTick 确保 UI 更新
              nextTick(() => {
                console.log('[DEBUG] NextTick executed, forcing UI update')
                console.log('[DEBUG] Message text in nextTick:', messages.value[lastIndex].text)
                console.log('[DEBUG] isReActRunning in nextTick:', isReActRunning.value)
              })
              scrollToBottom()
            } else if (parsed.type === 'react_steps') {
              // 最终步骤列表
              isReActRunning.value = false
              loading.value = false
              streaming.value = false
            } else if (parsed.type === 'react_error') {
              isReActRunning.value = false
              loading.value = false
              streaming.value = false
              console.error('[ReAct] Error:', parsed.message)
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }
    
    // 保存助手消息到数据库
    if (fullText) {
      const lastIndex = messages.value.length - 1
      // 确保 assistant 消息包含完整的元数据
      messages.value[lastIndex].had_tool_calls = !!(messages.value[lastIndex].reactSteps && messages.value[lastIndex].reactSteps.length > 0)

      const savedAssistantMessage = await saveMessageToDatabase('assistant', fullText, sources)
      if (savedAssistantMessage) {
        messages.value[lastIndex].id = savedAssistantMessage.id
      }
    }
    
  } catch (error) {
    console.error('Error:', error)
    const lastIndex = messages.value.length - 1
    messages.value[lastIndex].text = '抱歉，发生了错误。请检查网络连接或稍后重试。'
  } finally {
    console.log('[DEBUG] Finally block executed, resetting all states')
    loading.value = false
    streaming.value = false
    isReActRunning.value = false
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
    // 只刷新会话列表（更新预览信息），不重新加载消息（避免丢失正在流式传输的助手消息）
    await store.refreshSessionList()
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

/* Markdown 内容样式 - 与设计 token 对齐 */
:deep(.markdown-content) {
  line-height: 1.8;
  color: #0f172a;
}

:deep(.markdown-content h1) {
  font-size: 1.75rem;
  font-weight: 800;
  color: #0f172a;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e2e8f0;
  letter-spacing: -0.02em;
}

:deep(.markdown-content h2) {
  font-size: 1.375rem;
  font-weight: 700;
  color: #1e293b;
  margin-top: 1.25rem;
  margin-bottom: 0.625rem;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid #e2e8f0;
  letter-spacing: -0.01em;
}

:deep(.markdown-content h3) {
  font-size: 1.15rem;
  font-weight: 600;
  color: #334155;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
  font-size: 1.05rem;
  font-weight: 600;
  color: #475569;
  margin-top: 0.875rem;
  margin-bottom: 0.375rem;
}

:deep(.markdown-content p) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  color: #1e293b;
}

:deep(.markdown-content strong) {
  font-weight: 700;
  color: #0f172a;
}

:deep(.markdown-content em) {
  font-style: italic;
  color: #334155;
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
  color: #1e293b;
}

:deep(.markdown-content ul li::marker),
:deep(.markdown-content ol li::marker) {
  color: #4f46e5;
  font-weight: 600;
}

:deep(.markdown-content code) {
  background-color: #f1f5f9;
  color: #dc2626;
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85rem;
}

:deep(.markdown-content pre) {
  background-color: #1e293b;
  color: #f1f5f9;
  padding: 1rem;
  border-radius: 0.75rem;
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
  border-left: 4px solid #4f46e5;
  padding-left: 1rem;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  color: #475569;
  font-style: italic;
  background-color: #eef2ff;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  padding-right: 0.75rem;
  border-radius: 0 0.375rem 0.375rem 0;
}

:deep(.markdown-content a) {
  color: #4f46e5;
  text-decoration: underline;
  text-underline-offset: 2px;
}

:deep(.markdown-content a:hover) {
  color: #4338ca;
}

:deep(.markdown-content table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-content th),
:deep(.markdown-content td) {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

:deep(.markdown-content th) {
  background-color: #f8fafc;
  font-weight: 600;
  color: #1e293b;
}

:deep(.markdown-content tr:nth-child(even)) {
  background-color: #f8fafc;
}

:deep(.markdown-content tr:hover) {
  background-color: #f1f5f9;
}

:deep(.markdown-content hr) {
  border: none;
  height: 1px;
  background-color: #e2e8f0;
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

/* 用户消息文本选中样式 - 确保选中时能清晰看到 */
.user-select-text::selection {
  background-color: #4f46e5;
  color: #ffffff;
}

.user-select-text::-moz-selection {
  background-color: #4f46e5;
  color: #ffffff;
}
</style>
