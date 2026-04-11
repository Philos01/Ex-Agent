import React, { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'

export default function Chat({ onSessionEnd, initialMessages, initialParams, onMessagesChange, onParamsChange }) {
  const [q, setQ] = useState('')
  const [messages, setMessages] = useState(initialMessages || [])
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [params, setParams] = useState(initialParams || {
    top_k: 5,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  })
  const [showSidebar, setShowSidebar] = useState(false)
  const endRef = useRef(null)
  const scrollRef = useRef(null)

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [])

  // 当消息变化时滚动到底部
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // 当initialMessages变化时更新本地状态 - 使用useRef避免无限循环
  const initialMessagesRef = useRef(initialMessages)
  useEffect(() => {
    if (initialMessages !== initialMessagesRef.current) {
      initialMessagesRef.current = initialMessages
      setMessages(initialMessages || [])
    }
  }, [initialMessages])

  // 当消息变化时通知父组件 - 使用useCallback包装
  const notifyMessagesChange = useCallback((newMessages) => {
    if (onMessagesChange) {
      onMessagesChange(newMessages)
    }
  }, [onMessagesChange])

  // 使用useEffect来调用通知函数，避免直接在setMessages回调中调用
  useEffect(() => {
    notifyMessagesChange(messages)
  }, [messages, notifyMessagesChange])

  // 组件卸载时保存会话
  useEffect(() => {
    return () => {
      if (onSessionEnd && messages.length > 0) {
        onSessionEnd({ messages })
      }
    }
  }, [messages, onSessionEnd])

  // 参数更新处理
  const handleParamChange = (key, value) => {
    const newParams = { ...params, [key]: value }
    setParams(newParams)
    if (onParamsChange) {
      onParamsChange(newParams)
    }
  }

  const resetParams = () => {
    const defaultParams = {
      top_k: 5,
      temperature: 0.7,
      top_p: 0.9,
      max_tokens: 2048,
      presence_penalty: 0.0,
      frequency_penalty: 0.0
    }
    setParams(defaultParams)
    if (onParamsChange) {
      onParamsChange(defaultParams)
    }
  }

  // 流式发送消息 - 使用fetch API
  const sendStream = async () => {
    if (!q || loading || streaming) return
    
    const userMsg = {
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      user: '钟'
    }
    
    setMessages(m => [...m, userMsg])
    setQ('')
    setLoading(true)
    setStreaming(true)

    // 创建空的助手消息
    const assistantMsg = {
      role: 'assistant',
      text: '',
      timestamp: '正在生成...',
      sources: []
    }
    setMessages(m => [...m, assistantMsg])

    try {
      const response = await fetch('/api/qa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: q, 
          stream: true,
          ...params
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''
      let currentSources = []
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'sources') {
                currentSources = data.data
              } else if (data.type === 'content') {
                fullText += data.data
                setMessages(m => {
                  const newMessages = [...m]
                  const lastMessage = newMessages[newMessages.length - 1]
                  if (lastMessage && lastMessage.role === 'assistant') {
                    newMessages[newMessages.length - 1] = {
                      ...lastMessage,
                      text: fullText,
                      timestamp: '刚刚',
                      sources: currentSources
                    }
                  }
                  return newMessages
                })
              } else if (data.type === 'done') {
                setLoading(false)
                setStreaming(false)
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }

      // 确保最终状态正确
      setLoading(false)
      setStreaming(false)

    } catch (e) {
      console.error('Stream error:', e)
      setLoading(false)
      setStreaming(false)
      setMessages(m => {
        const newMessages = [...m]
        const lastMessage = newMessages[newMessages.length - 1]
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.text === '') {
          newMessages[newMessages.length - 1] = {
            ...lastMessage,
            text: '连接失败，请检查网络连接。',
            timestamp: '刚刚',
            sources: []
          }
        }
        return newMessages
      })
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendStream()
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="flex flex-1 overflow-hidden">
        {/* 主聊天区域 */}
        <div className="flex flex-col flex-1">
          {/* 聊天消息区域 */}
          <section 
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-12 py-10 space-y-10 scroll-smooth chat-scrollbar"
          >
            {/* 欢迎界面 */}
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full max-w-4xl mx-auto text-center">
                <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-5xl text-primary">psychology</span>
                </div>
                <h2 className="text-3xl font-bold text-on-surface mb-3">欢迎使用 Ex-Agent</h2>
                <p className="text-lg text-on-surface-variant max-w-lg mb-8">
                  您的智能通用助手已就绪。上传文档到知识库，然后开始提问吧！
                </p>
                <div className="flex gap-4">
                  <button 
                    onClick={() => {}}
                    className="px-6 py-3 bg-surface-container-highest text-on-surface rounded-xl font-bold hover:bg-surface-container-highest/80 transition-colors"
                  >
                    查看示例问题
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* User Message */}
                {messages.map((m, i) => (
                  <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'} w-full max-w-4xl mx-auto`}>
                    {m.role === 'user' ? (
                      <>
                        <div className="bg-surface-container-highest text-on-surface px-6 py-4 rounded-2xl rounded-tr-none shadow-sm max-w-[80%] leading-relaxed">
                          {m.text}
                        </div>
                        <span className="text-[10px] mt-2 font-bold text-on-surface-variant tracking-wider uppercase">
                          {m.user} • {m.timestamp}
                        </span>
                      </>
                    ) : (
                      <>
                        <div className="bg-surface-container-lowest border border-outline-variant/10 px-8 py-7 rounded-2xl rounded-tl-none shadow-sm max-w-[90%] relative">
                          <div className="flex items-center gap-2 mb-4 text-primary">
                            <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: 'FILL 1' }}>auto_awesome</span>
                            <span className="text-xs font-black uppercase tracking-tighter">Ex-Agent 分析报告</span>
                          </div>
                          <div className="space-y-4 text-on-surface-variant leading-relaxed text-[15px]">
                            <p>{m.text}</p>
                            {m.sources && m.sources.length > 0 && (
                              <div className="bg-surface-container-low p-5 rounded-xl space-y-3">
                                <h4 className="text-xs font-bold uppercase tracking-widest text-on-surface">引用来源</h4>
                                <div className="flex flex-wrap gap-2">
                                  {(() => {
                                    const uniqueSources = [];
                                    const seen = new Set();
                                    m.sources.forEach((source) => {
                                      const key = source.source || source.filename || `文档`;
                                      if (!seen.has(key)) {
                                        seen.add(key);
                                        uniqueSources.push(source);
                                      }
                                    });
                                    return uniqueSources.map((source, index) => (
                                      <div key={index} className="bg-secondary-container text-on-secondary-container px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5">
                                        <span className="material-symbols-outlined text-[14px]">picture_as_pdf</span>
                                        {source.source || source.filename || `文档 ${index + 1}`}
                                      </div>
                                    ));
                                  })()}
                                </div>
                              </div>
                            )}
                          </div>
                          {(loading || streaming) && i === messages.length - 1 && m.role === 'assistant' && (
                            <div className="absolute bottom-2 right-2 flex items-center gap-1.5">
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                          )}
                        </div>
                        <span className="text-[10px] mt-2 font-bold text-primary tracking-wider uppercase ml-1">
                          Ex-Agent 通用助手 • {m.timestamp}
                        </span>
                      </>
                    )}
                  </div>
                ))}
              </>
            )}

            <div ref={endRef}></div>
          </section>

          {/* 输入区域 */}
          <footer className="px-12 py-8 bg-surface/50 backdrop-blur-md">
            <div className="max-w-4xl mx-auto relative group">
              <div className="absolute inset-0 bg-primary/5 blur-xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
              <div className="relative flex items-end gap-4 bg-surface-container-lowest p-3 rounded-2xl shadow-lg shadow-on-surface/[0.03] border border-outline-variant/20 focus-within:border-primary/40 transition-all">
                <textarea 
                  value={q} 
                  onChange={e => setQ(e.target.value)} 
                  onKeyDown={handleKeyDown}
                  className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-outline/60 py-3 resize-none font-medium leading-relaxed"
                  placeholder="向 Ex-Agent 咨询实验结果、趋势或方案..."
                  rows={1}
                  disabled={loading || streaming}
                />
                <button 
                  onClick={sendStream} 
                  disabled={loading || streaming}
                  className="h-12 w-12 bg-black text-white rounded-xl flex items-center justify-center shadow-lg shadow-black/20 transition-transform active:scale-90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="material-symbols-outlined">send</span>
                </button>
              </div>
              <div className="flex justify-between px-4 mt-3">
                <div className="flex items-center gap-4">
                  <span className="text-[10px] font-bold text-outline uppercase flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-primary-container rounded-full animate-pulse"></span>
                    {(loading || streaming) ? '正在生成...' : 'AI 就绪'}
                  </span>
                </div>
              </div>
            </div>
          </footer>
        </div>

        {/* 右侧参数设置面板 */}
        <aside className={`bg-surface border-l border-outline-variant/20 overflow-y-auto chat-scrollbar transition-all duration-300 ${showSidebar ? 'w-80' : 'w-0 border-0'}`}>
          {showSidebar && (
            <div className="p-6 space-y-8">
              {/* 面板头部 */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-on-surface">运行设置</h3>
                <button 
                  onClick={() => setShowSidebar(false)}
                  className="p-1 rounded-lg hover:bg-surface-container-high transition-colors"
                >
                  <span className="material-symbols-outlined text-on-surface-variant">close</span>
                </button>
              </div>

              {/* Top K */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">检索文档数</h4>
                    <p className="text-xs text-on-surface-variant">Top K</p>
                  </div>
                  <span className="text-lg font-bold text-primary">{params.top_k}</span>
                </div>
                <input 
                  type="range" 
                  min="1" 
                  max="20" 
                  step="1"
                  value={params.top_k}
                  onChange={(e) => handleParamChange('top_k', parseInt(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-primary"
                />
              </div>

              {/* Temperature */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">温度</h4>
                    <p className="text-xs text-on-surface-variant">Temperature</p>
                  </div>
                  <span className="text-lg font-bold text-tertiary">{params.temperature}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="2" 
                  step="0.1"
                  value={params.temperature}
                  onChange={(e) => handleParamChange('temperature', parseFloat(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-tertiary"
                />
              </div>

              {/* Top P */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">Top P</h4>
                    <p className="text-xs text-on-surface-variant">Nucleus sampling</p>
                  </div>
                  <span className="text-lg font-bold text-primary">{params.top_p}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.05"
                  value={params.top_p}
                  onChange={(e) => handleParamChange('top_p', parseFloat(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-primary"
                />
              </div>

              {/* Max Tokens */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">最大令牌数</h4>
                    <p className="text-xs text-on-surface-variant">Max response length</p>
                  </div>
                  <span className="text-lg font-bold text-secondary">{params.max_tokens}</span>
                </div>
                <input 
                  type="range" 
                  min="256" 
                  max="8192" 
                  step="256"
                  value={params.max_tokens}
                  onChange={(e) => handleParamChange('max_tokens', parseInt(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-secondary"
                />
              </div>

              {/* Presence Penalty */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">存在惩罚</h4>
                    <p className="text-xs text-on-surface-variant">Presence penalty</p>
                  </div>
                  <span className="text-lg font-bold">{params.presence_penalty}</span>
                </div>
                <input 
                  type="range" 
                  min="-2" 
                  max="2" 
                  step="0.1"
                  value={params.presence_penalty}
                  onChange={(e) => handleParamChange('presence_penalty', parseFloat(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer"
                />
              </div>

              {/* Frequency Penalty */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-on-surface">频率惩罚</h4>
                    <p className="text-xs text-on-surface-variant">Frequency penalty</p>
                  </div>
                  <span className="text-lg font-bold">{params.frequency_penalty}</span>
                </div>
                <input 
                  type="range" 
                  min="-2" 
                  max="2" 
                  step="0.1"
                  value={params.frequency_penalty}
                  onChange={(e) => handleParamChange('frequency_penalty', parseFloat(e.target.value))}
                  className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer"
                />
              </div>

              {/* 重置按钮 */}
              <div className="pt-4 border-t border-outline-variant/20">
                <button 
                  onClick={resetParams}
                  className="w-full py-2.5 text-sm font-semibold text-primary bg-primary/10 rounded-lg hover:bg-primary/20 transition-colors"
                >
                  重置为默认值
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* 参数设置开关按钮 - 固定在右侧 */}
      {!showSidebar && (
        <button
          onClick={() => setShowSidebar(true)}
          className="fixed right-4 top-1/2 -translate-y-1/2 z-50 p-3 bg-surface border border-outline-variant/20 rounded-xl shadow-lg hover:bg-surface-container-high transition-all"
        >
          <span className="material-symbols-outlined text-on-surface">settings</span>
        </button>
      )}
    </div>
  )
}
