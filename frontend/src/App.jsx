import React, { useState, useEffect, useCallback } from 'react'
import Chat from './components/Chat'
import Uploads from './components/Uploads'
import Settings from './components/Settings'
import ErrorBoundary from './components/ErrorBoundary'

// 全局状态管理
const AppContext = React.createContext()

// 安全的localStorage操作
const safeLocalStorage = {
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value)
      return true
    } catch (e) {
      console.warn('localStorage quota exceeded, cleaning up old data...')
      try {
        // 尝试清理旧数据
        const oldSessions = localStorage.getItem('luminar_sessions')
        if (oldSessions) {
          const sessions = JSON.parse(oldSessions)
          // 只保留最近10个会话
          const trimmedSessions = sessions.slice(0, 10)
          localStorage.setItem('luminar_sessions', JSON.stringify(trimmedSessions))
          // 重试保存
          localStorage.setItem(key, value)
          return true
        }
      } catch (cleanupError) {
        console.error('Failed to clean up localStorage:', cleanupError)
      }
      return false
    }
  },
  getItem: (key) => {
    try {
      return localStorage.getItem(key)
    } catch (e) {
      console.error('Failed to read from localStorage:', e)
      return null
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.error('Failed to remove from localStorage:', e)
    }
  }
}

export default function App() {
  const [tab, setTab] = useState('chat')
  const [chatKey, setChatKey] = useState(Date.now()) // 用于触发新建会话
  const [sessions, setSessions] = useState([]) // 存储会话历史
  const [chatMessages, setChatMessages] = useState([]) // 持久化聊天消息
  const [chatParams, setChatParams] = useState({ // 聊天参数
    top_k: 5,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  })

  // 从localStorage加载数据
  useEffect(() => {
    const savedSessions = safeLocalStorage.getItem('luminar_sessions')
    const savedMessages = safeLocalStorage.getItem('luminar_current_chat')
    
    if (savedSessions) {
      try {
        setSessions(JSON.parse(savedSessions))
      } catch (e) {
        console.error('Failed to parse sessions:', e)
      }
    }
    
    if (savedMessages) {
      try {
        setChatMessages(JSON.parse(savedMessages))
      } catch (e) {
        console.error('Failed to parse chat messages:', e)
      }
    }
  }, [])

  // 保存会话到localStorage - 使用useCallback避免依赖问题
  const saveSessionsToStorage = useCallback((newSessions) => {
    // 限制会话数量
    const trimmedSessions = newSessions.slice(0, 20)
    safeLocalStorage.setItem('luminar_sessions', JSON.stringify(trimmedSessions))
  }, [])

  // 保存当前聊天到localStorage - 使用useCallback
  const updateChatMessages = useCallback((messages) => {
    setChatMessages(messages)
    safeLocalStorage.setItem('luminar_current_chat', JSON.stringify(messages))
  }, [])

  // 新建会话功能
  const createNewAnalysis = () => {
    // 如果当前有聊天内容，先保存到会话历史
    if (chatMessages.length > 0) {
      const session = {
        id: Date.now(),
        timestamp: new Date().toLocaleString('zh-CN'),
        messages: chatMessages
      }
      const newSessions = [session, ...sessions]
      setSessions(newSessions)
      saveSessionsToStorage(newSessions)
    }
    
    // 清空当前聊天
    setChatMessages([])
    safeLocalStorage.removeItem('luminar_current_chat')
    
    // 生成新的会话ID
    const newSessionId = Date.now()
    // 更新chatKey以重新渲染Chat组件
    setChatKey(newSessionId)
    // 切换到聊天页面
    setTab('chat')
  }

  // 保存会话
  const saveSession = (sessionData) => {
    if (!sessionData || sessionData.messages.length === 0) return
    
    // 首先保存到当前聊天
    setChatMessages(sessionData.messages)
    safeLocalStorage.setItem('luminar_current_chat', JSON.stringify(sessionData.messages))
    
    const session = {
      id: Date.now(),
      timestamp: new Date().toLocaleString('zh-CN'),
      ...sessionData
    }
    
    const newSessions = [session, ...sessions]
    setSessions(newSessions)
    saveSessionsToStorage(newSessions)
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-surface text-on-surface">
        {/* 侧边栏导航 */}
        <aside className="h-screen w-64 fixed left-0 top-0 bg-[#e6e8ea] dark:bg-slate-900 flex flex-col p-4 space-y-6 z-40">
          <div className="flex items-center space-x-3 mb-4 px-2">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined">biotech</span>
            </div>
            <div>
              <h1 className="text-lg font-black text-[#006b5f] leading-tight">Ex-Agent</h1>
              <p className="text-[10px] font-semibold tracking-wider text-on-surface-variant opacity-70 uppercase">Precision Lab OS</p>
            </div>
          </div>
          <button onClick={createNewAnalysis} className="w-full py-3 px-4 bg-gradient-to-br from-primary to-primary-container text-on-black rounded-xl font-bold shadow-lg shadow-primary/20 flex items-center justify-center space-x-2 active:scale-95 transition-transform">
            <span className="material-symbols-outlined text-[20px]">add</span>
            <span className="font-manrope text-sm font-semibold tracking-wide">新建会话</span>
          </button>
        <nav className="flex-1 space-y-1">
          <button 
            onClick={() => setTab('chat')} 
            className={`flex items-center space-x-3 px-4 py-3 ${tab === 'chat' ? 'bg-white dark:bg-slate-800 text-[#006b5f] rounded-lg shadow-sm font-bold' : 'text-slate-600 dark:text-slate-400 hover:bg-[#f2f4f6] dark:hover:bg-slate-800 rounded-lg transition-all group'}`}
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors" style={{ fontVariationSettings: tab === 'chat' ? 'FILL 1' : 'FILL 0' }}>chat_bubble</span>
            <span className="font-manrope text-sm font-semibold tracking-wide">对话</span>
          </button>
          <button 
            onClick={() => setTab('uploads')} 
            className={`flex items-center space-x-3 px-4 py-3 ${tab === 'uploads' ? 'bg-white dark:bg-slate-800 text-[#006b5f] rounded-lg shadow-sm font-bold' : 'text-slate-600 dark:text-slate-400 hover:bg-[#f2f4f6] dark:hover:bg-slate-800 rounded-lg transition-all group'}`}
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors" style={{ fontVariationSettings: tab === 'uploads' ? 'FILL 1' : 'FILL 0' }}>database</span>
            <span className="font-manrope text-sm font-semibold tracking-wide">知识库</span>
          </button>
          <button 
            onClick={() => setTab('settings')} 
            className={`flex items-center space-x-3 px-4 py-3 ${tab === 'settings' ? 'bg-white dark:bg-slate-800 text-[#006b5f] rounded-lg shadow-sm font-bold' : 'text-slate-600 dark:text-slate-400 hover:bg-[#f2f4f6] dark:hover:bg-slate-800 rounded-lg transition-all group'}`}
          >
            <span className="material-symbols-outlined group-hover:text-primary transition-colors" style={{ fontVariationSettings: tab === 'settings' ? 'FILL 1' : 'FILL 0' }}>settings</span>
            <span className="font-manrope text-sm font-semibold tracking-wide">设置</span>
          </button>
        </nav>
        <div className="pt-4 border-t border-outline-variant/10 space-y-1">
          <a className="flex items-center space-x-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-[#f2f4f6] dark:hover:bg-slate-800 rounded-lg transition-all" href="#">
            <span className="material-symbols-outlined">logout</span>
            <span className="font-manrope text-sm font-semibold tracking-wide">退出登录</span>
          </a>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main className="ml-64 min-h-screen">
        {/* 顶部栏 */}
        <header className="flex justify-between items-center px-8 w-full sticky top-0 z-30 h-16 bg-[#f7f9fb] transition-colors duration-200">
          <div className="flex items-center space-x-4">
            <h2 className="font-manrope text-xl font-bold tracking-tighter text-[#006b5f] dark:text-[#04ae9c]">
              {tab === 'chat' && 'Remote Sense 通用助手'}
              {tab === 'uploads' && 'RS AI'}
              {tab === 'settings' && '系统设置'}
            </h2>
            {tab === 'settings' && (
              <div className="px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold uppercase tracking-widest">v2.4.0-Stable</div>
            )}
            {tab === 'uploads' && (
              <>
                <div className="h-4 w-px bg-outline-variant opacity-30"></div>
                <div className="flex items-center gap-2 text-on-surface-variant font-medium text-sm tracking-tight">
                  <span className="material-symbols-outlined text-base">folder_open</span>
                  知识库 / 资产
                </div>
              </>
            )}
            {tab === 'chat' && (
              <>
                <div className="h-4 w-px bg-outline-variant/30"></div>
                <span className="text-sm font-medium text-on-surface-variant">会话</span>
              </>
            )}
          </div>
          <div className="flex items-center space-x-4 text-slate-500">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="material-symbols-outlined text-[20px]">help_outline</span>
          </div>
        </header>

        {/* 内容区域 */}
        <div className="flex-1 overflow-auto">
          {tab === 'chat' && <Chat 
            key={chatKey} 
            initialMessages={chatMessages}
            initialParams={chatParams}
            onMessagesChange={updateChatMessages}
            onParamsChange={setChatParams}
            onSessionEnd={saveSession} 
          />}
          {tab === 'uploads' && <Uploads />}
          {tab === 'settings' && <Settings />}
        </div>
      </main>

      {/* 浮动装饰 */}
      <div className="fixed top-20 right-[-100px] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -z-10"></div>
      <div className="fixed bottom-0 left-[-50px] w-[300px] h-[300px] bg-secondary-container/10 rounded-full blur-[100px] pointer-events-none -z-10"></div>
      </div>
    </ErrorBoundary>
  )
}
