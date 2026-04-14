import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sessionService } from '../services/sessions'

export const useAppStore = defineStore('app', () => {
  // 状态
  const currentView = ref('chat')
  const sessionHistory = ref([])
  const currentSessionId = ref(null)
  const chatMessages = ref([])
  const chatParams = ref(localStorage.getItem('luminar_params') ? JSON.parse(localStorage.getItem('luminar_params')) : {
    top_k: 5,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  })
  const isLoading = ref(false)
  const isSessionsLoaded = ref(false)
  const isInitialized = ref(false)

  // 计算属性
  const currentSession = computed(() => 
    sessionHistory.value.find(s => s.id === currentSessionId.value)
  )

  // 从数据库加载会话列表
  async function loadSessionsFromDatabase() {
    try {
      isLoading.value = true
      console.log('[DEBUG] Loading sessions from database...')
      const sessions = await sessionService.getSessions()
      sessionHistory.value = sessions
      isSessionsLoaded.value = true
      console.log('[DEBUG] Sessions loaded:', sessions.length)
      
      // 如果有会话，选中第一个
      if (sessions.length > 0 && !currentSessionId.value) {
        currentSessionId.value = sessions[0].id
        await loadSessionMessages(sessions[0].id)
      }
    } catch (error) {
      console.error('[ERROR] Failed to load sessions:', error)
    } finally {
      isLoading.value = false
    }
  }

  // 格式化时间为北京时间 HH:MM
  function formatBeijingTime(timeValue) {
    if (!timeValue) {
      return '--:--'
    }
    // 如果已经是格式化的时间字符串，直接返回
    if (typeof timeValue === 'string' && timeValue.includes(':') && !timeValue.includes('T')) {
      return timeValue
    }
    try {
      const date = new Date(timeValue)
      if (!isNaN(date.getTime())) {
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

  // 加载会话消息
  async function loadSessionMessages(sessionId) {
    try {
      console.log('[DEBUG] Loading session messages for:', sessionId)
      const result = await sessionService.getSession(sessionId)
      // 确保正确处理返回的数据结构
      const messages = result.messages || []
      console.log('[DEBUG] Messages received from API:', messages.length)
      chatMessages.value = messages.map(m => {
        return {
          id: m.id,
          role: m.role,
          text: m.content,
          time: formatBeijingTime(m.created_at),
          sources: m.sources
        }
      })
      currentSessionId.value = sessionId
      console.log('[DEBUG] Session messages loaded:', chatMessages.value.length)
    } catch (error) {
      console.error('[ERROR] Failed to load session messages:', error)
    }
  }

  // 方法
  function setView(view) {
    currentView.value = view
  }

  async function createNewSession() {
    try {
      console.log('[DEBUG] Creating new session...')
      const newSession = await sessionService.createSession('新会话')
      
      // 保存当前会话
      if (chatMessages.value.length > 0 && currentSessionId.value) {
        await saveCurrentSessionToDatabase()
      }
      
      // 添加到会话列表开头
      sessionHistory.value.unshift(newSession)
      
      // 创建新会话
      currentSessionId.value = newSession.id
      chatMessages.value = []
      
      console.log('[DEBUG] New session created:', newSession)
    } catch (error) {
      console.error('[ERROR] Failed to create new session:', error)
    }
  }

  async function saveCurrentSessionToDatabase() {
    if (chatMessages.value.length === 0 || !currentSessionId.value) return
    
    try {
      console.log('[DEBUG] Saving current session to database...')
      
      // 保存所有未保存的消息
      for (const message of chatMessages.value) {
        // 检查消息是否已保存（简单判断：如果消息没有id，则认为未保存）
        if (!message.id) {
          await sessionService.addMessage(
            currentSessionId.value,
            message.role,
            message.text,
            message.sources
          )
        }
      }
      
      // 重新加载会话列表以获取更新的信息
      await loadSessionsFromDatabase()
      
      console.log('[DEBUG] Session saved to database')
    } catch (error) {
      console.error('[ERROR] Failed to save session to database:', error)
    }
  }

  async function loadSession(sessionId) {
    console.log('[DEBUG] Loading session:', sessionId)
    await loadSessionMessages(sessionId)
  }

  async function deleteSession(sessionId) {
    try {
      console.log('[DEBUG] Deleting session:', sessionId)
      await sessionService.deleteSession(sessionId)
      
      // 从本地列表中移除
      sessionHistory.value = sessionHistory.value.filter(s => s.id !== sessionId)
      
      // 如果删除的是当前会话，切换到第一个会话或清空
      if (currentSessionId.value === sessionId) {
        if (sessionHistory.value.length > 0) {
          await loadSession(sessionHistory.value[0].id)
        } else {
          currentSessionId.value = null
          chatMessages.value = []
        }
      }
      
      console.log('[DEBUG] Session deleted:', sessionId)
    } catch (error) {
      console.error('[ERROR] Failed to delete session:', error)
    }
  }

  function updateChatMessages(messages) {
    chatMessages.value = messages
  }

  function updateChatParams(params) {
    chatParams.value = { ...chatParams.value, ...params }
    localStorage.setItem('luminar_params', JSON.stringify(chatParams.value))
  }

  // 重置应用状态（用于登出或切换用户时）
  function resetState() {
    console.log('[DEBUG] Resetting app store state...')
    currentView.value = 'chat'
    sessionHistory.value = []
    currentSessionId.value = null
    chatMessages.value = []
    isLoading.value = false
    isSessionsLoaded.value = false
    isInitialized.value = false
    console.log('[DEBUG] App store state reset complete')
  }

  // 初始化
  function init() {
    console.log('[DEBUG] Initializing app store...')
    loadSessionsFromDatabase()
  }

  return {
    // 状态
    currentView,
    sessionHistory,
    currentSessionId,
    chatMessages,
    chatParams,
    isLoading,
    isSessionsLoaded,
    isInitialized,
    
    // 计算属性
    currentSession,
    
    // 方法
    setView,
    createNewSession,
    loadSession,
    deleteSession,
    updateChatMessages,
    updateChatParams,
    saveCurrentSessionToDatabase,
    loadSessionsFromDatabase,
    init,
    resetState
  }
})
