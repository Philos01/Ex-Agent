import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function Settings() {
  const [cfg, setCfg] = useState({
    provider: 'openai',
    openai_api_key: '',
    openai_base_url: 'https://api.openai-hk.com/v1',
    openai_embedding_model: 'text-embedding-3-small',
    openai_chat_model: 'gpt-3.5-turbo',
    ollama_url: 'http://localhost:11434',
    ollama_model: '',
    chunk_size: 1500,
    chunk_overlap: 100,
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    presence_penalty: 0.0,
    frequency_penalty: 0.0
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  
  useEffect(() => { load() }, [])
  
  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const r = await axios.get('/api/config')
      setCfg(r.data)
    } catch (e) {
      console.error(e)
      setError('加载配置失败：' + (e.message || e))
      // 如果加载失败，使用默认配置（推荐最佳设置）
      setCfg({
        provider: 'openai',
        openai_api_key: '',
        openai_base_url: 'https://api.openai-hk.com/v1',
        openai_embedding_model: 'text-embedding-3-small',
        openai_chat_model: 'gpt-3.5-turbo',
        ollama_url: 'http://localhost:11434',
        ollama_model: '',
        chunk_size: 1500,
        chunk_overlap: 100,
        temperature: 0.7,
        top_p: 0.9,
        max_tokens: 2048,
        presence_penalty: 0.0,
        frequency_penalty: 0.0
      })
    } finally {
      setLoading(false)
    }
  }
  
  const validate = () => {
    if (cfg.provider === 'openai' && !cfg.openai_api_key.trim()) {
      setError('请输入OpenAI API密钥')
      return false
    }
    if (cfg.provider === 'ollama') {
      if (!cfg.ollama_url.trim()) {
        setError('请输入Ollama服务URL')
        return false
      }
      if (!cfg.ollama_model.trim()) {
        setError('请输入Ollama模型名称')
        return false
      }
    }
    setError('')
    return true
  }
  
  const save = async () => {
    if (!validate()) return
    
    setSaving(true)
    setError('')
    try {
      await axios.post('/api/config', cfg)
      alert('配置已成功保存！')
    } catch (e) {
      console.error(e)
      const errorMsg = e.response?.data?.detail || e.message || '未知错误'
      setError('保存失败：' + errorMsg)
    } finally {
      setSaving(false)
    }
  }
  
  const handleProviderChange = (provider) => {
    setCfg(prev => ({...prev, provider: provider}))
  }
  
  const handleApiKeyChange = (e) => {
    setCfg(prev => ({...prev, openai_api_key: e.target.value}))
  }
  
  const handleOllamaUrlChange = (e) => {
    setCfg(prev => ({...prev, ollama_url: e.target.value}))
  }
  
  const handleOllamaModelChange = (e) => {
    setCfg(prev => ({...prev, ollama_model: e.target.value}))
  }
  
  const handleChunkSizeChange = (e) => {
    setCfg(prev => ({...prev, chunk_size: parseInt(e.target.value)}))
  }
  
  const handleOverlapChange = (e) => {
    setCfg(prev => ({...prev, chunk_overlap: parseInt(e.target.value)}))
  }
  
  const handleTemperatureChange = (e) => {
    setCfg(prev => ({...prev, temperature: parseFloat(e.target.value)}))
  }

  const handleBaseUrlChange = (e) => {
    setCfg(prev => ({...prev, openai_base_url: e.target.value}))
  }
  
  const handleOpenAIChatModelChange = (e) => {
    setCfg(prev => ({...prev, openai_chat_model: e.target.value}))
  }
  
  const handleTopPChange = (e) => {
    setCfg(prev => ({...prev, top_p: parseFloat(e.target.value)}))
  }
  
  const handleMaxTokensChange = (e) => {
    setCfg(prev => ({...prev, max_tokens: parseInt(e.target.value)}))
  }
  
  const handlePresencePenaltyChange = (e) => {
    setCfg(prev => ({...prev, presence_penalty: parseFloat(e.target.value)}))
  }
  
  const handleFrequencyPenaltyChange = (e) => {
    setCfg(prev => ({...prev, frequency_penalty: parseFloat(e.target.value)}))
  }
  
  return (
    <div className="p-8 max-w-6xl mx-auto space-y-12">
      {/* Section 1: LLM Engine */}
      <section className="space-y-6">
        <div className="flex items-baseline space-x-4">
          <h3 className="text-3xl font-light tracking-tight text-on-surface">大语言模型引擎 <span className="font-bold text-primary">供应商</span></h3>
          <div className="h-px flex-1 bg-gradient-to-r from-outline-variant/30 to-transparent"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* OpenAI Provider Card */}
          <div 
            className={`relative cursor-pointer p-6 rounded-xl bg-surface-container-lowest border-2 transition-all duration-300 shadow-sm ${cfg.provider === 'openai' ? 'border-primary shadow-primary/5' : 'border-transparent'}`}
            onClick={() => handleProviderChange('openai')}
          >
            <div className="flex items-start justify-between mb-8">
              <div className="w-12 h-12 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-3xl">hub</span>
              </div>
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${cfg.provider === 'openai' ? 'bg-primary border-primary' : 'border-outline-variant'}`}>
                {cfg.provider === 'openai' && <div className="w-2 h-2 bg-white rounded-full"></div>}
              </div>
            </div>
            <h4 className="text-lg font-bold mb-1">OpenAI 云端</h4>
            <p className="text-sm text-on-surface-variant leading-relaxed">Enterprise-grade performance. Required for complex reasoning and large-scale analysis.</p>
          </div>
          {/* Ollama Provider Card */}
          <div 
            className={`relative cursor-pointer p-6 rounded-xl bg-surface-container-lowest border-2 transition-all duration-300 shadow-sm ${cfg.provider === 'ollama' ? 'border-primary shadow-primary/5' : 'border-transparent'}`}
            onClick={() => handleProviderChange('ollama')}
          >
            <div className="flex items-start justify-between mb-8">
              <div className="w-12 h-12 rounded-lg bg-surface-container-high flex items-center justify-center text-on-surface-variant">
                <span className="material-symbols-outlined text-3xl">memory</span>
              </div>
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${cfg.provider === 'ollama' ? 'bg-primary border-primary' : 'border-outline-variant'}`}>
                {cfg.provider === 'ollama' && <div className="w-2 h-2 bg-white rounded-full"></div>}
              </div>
            </div>
            <h4 className="text-lg font-bold mb-1">Ollama 本地</h4>
            <p className="text-sm text-on-surface-variant leading-relaxed">On-premise execution. Ideal for sensitive data compliance and air-gapped environments.</p>
          </div>
        </div>
      </section>
      {/* 错误消息 */}
        {error && (
          <div className="bg-error/10 border border-error/20 p-4 rounded-xl">
            <p className="text-error text-sm font-medium flex items-center gap-2">
              <span className="material-symbols-outlined">error</span>
              {error}
            </p>
          </div>
        )}
        
        {/* Section 2: API Configuration & RAG Bento */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* API Configuration Column */}
        <section className="lg:col-span-1 space-y-6">
          <h3 className="text-xl font-bold tracking-tight text-on-surface">API 凭证</h3>
          <div className="space-y-4">
            {cfg.provider === 'openai' && (
              <>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant ml-1">OpenAI API 基础URL</label>
                  <input 
                    className="w-full px-4 py-3 bg-surface-container-low border-b-2 border-transparent focus:border-primary focus:ring-0 rounded-lg transition-all text-sm font-medium" 
                    type="text" 
                    value={cfg.openai_base_url} 
                    onChange={handleBaseUrlChange}
                    placeholder="https://api.openai-hk.com/v1"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant ml-1">OpenAI API 密钥</label>
                  <div className="relative">
                    <input 
                      className="w-full px-4 py-3 bg-surface-container-low border-b-2 border-transparent focus:border-primary focus:ring-0 rounded-lg transition-all text-sm font-medium" 
                      type={showPassword ? 'text' : 'password'} 
                      value={cfg.openai_api_key} 
                      onChange={handleApiKeyChange}
                      placeholder="sk-..."
                    />
                    <button 
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-primary transition-colors"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      <span className="material-symbols-outlined text-lg">{showPassword ? 'visibility_off' : 'visibility'}</span>
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant ml-1">聊天模型</label>
                  <select 
                    className="w-full px-4 py-3 bg-surface-container-low border-b-2 border-transparent focus:border-primary focus:ring-0 rounded-lg transition-all text-sm font-medium"
                    value={cfg.openai_chat_model}
                    onChange={handleOpenAIChatModelChange}
                  >
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4o-mini">GPT-4o Mini</option>
                  </select>
                </div>
              </>
            )}
            {cfg.provider === 'ollama' && (
              <>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant ml-1">Ollama 服务 URL</label>
                  <input className="w-full px-4 py-3 bg-surface-container-low border-b-2 border-transparent focus:border-primary focus:ring-0 rounded-lg transition-all text-sm font-medium" placeholder="http://localhost:11434" type="text" value={cfg.ollama_url} onChange={handleOllamaUrlChange}/>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant ml-1">Ollama 模型</label>
                  <input className="w-full px-4 py-3 bg-surface-container-low border-b-2 border-transparent focus:border-primary focus:ring-0 rounded-lg transition-all text-sm font-medium" placeholder="例如: llama3" type="text" value={cfg.ollama_model} onChange={handleOllamaModelChange}/>
                </div>
              </>
            )}
          </div>
        </section>
        {/* RAG Tuning Bento Grid */}
        <section className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold tracking-tight text-on-surface">RAG 与神经元调优</h3>
            <span className="text-xs font-semibold text-primary flex items-center">
              <span className="material-symbols-outlined text-sm mr-1">info</span>
              Optimized for General NLP
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {/* Chunk Size (Asymmetric Large) */}
            <div className="col-span-2 p-6 rounded-2xl bg-surface-container-lowest shadow-sm flex flex-col justify-between space-y-8">
              <div className="flex justify-between items-start">
                <div>
                  <h5 className="font-bold text-on-surface">分块大小</h5>
                  <p className="text-xs text-on-surface-variant">Context window per retrieval</p>
                  {cfg.chunk_size === 1500 && (
                    <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                  )}
                </div>
                <span className="text-2xl font-black text-primary">{cfg.chunk_size}<span className="text-xs font-medium ml-1 text-on-surface-variant">令牌 (Tokens)</span></span>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-primary" max="2048" min="128" step="128" type="range" value={cfg.chunk_size} onChange={handleChunkSizeChange}/>
            </div>
            {/* Overlap (Small) */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">重叠度</h5>
                <p className="text-xs text-on-surface-variant">Semantic persistence</p>
                {cfg.chunk_overlap === 100 && (
                  <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-on-surface">{cfg.chunk_overlap}</span>
                <div className="flex space-x-1">
                  <div className="w-6 h-1 rounded-full bg-primary"></div>
                  <div className="w-6 h-1 rounded-full bg-primary/20"></div>
                  <div className="w-6 h-1 rounded-full bg-primary/20"></div>
                </div>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-primary" max="500" min="0" step="50" type="range" value={cfg.chunk_overlap} onChange={handleOverlapChange}/>
            </div>
            {/* Temperature (Small) */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">温度 (Temperature)</h5>
                <p className="text-xs text-on-surface-variant">Creative variance</p>
                {cfg.temperature === 0.7 && (
                  <span className="text-[10px] font-bold text-tertiary bg-tertiary/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-tertiary">{cfg.temperature}</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 rounded-full bg-tertiary"></div>
                  <div className="w-2 h-2 rounded-full bg-tertiary/20"></div>
                  <div className="w-2 h-2 rounded-full bg-tertiary/20"></div>
                </div>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-tertiary" max="2" min="0" step="0.1" type="range" value={cfg.temperature} onChange={handleTemperatureChange}/>
            </div>
            {/* Top P */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">Top P</h5>
                <p className="text-xs text-on-surface-variant">Nucleus sampling</p>
                {cfg.top_p === 0.9 && (
                  <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-primary">{cfg.top_p}</span>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-primary" max="1" min="0" step="0.05" type="range" value={cfg.top_p} onChange={handleTopPChange}/>
            </div>
            {/* Max Tokens */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">最大令牌数</h5>
                <p className="text-xs text-on-surface-variant">Maximum response length</p>
                {cfg.max_tokens === 2048 && (
                  <span className="text-[10px] font-bold text-secondary bg-secondary/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold text-secondary">{cfg.max_tokens}</span>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer accent-secondary" max="8192" min="256" step="256" type="range" value={cfg.max_tokens} onChange={handleMaxTokensChange}/>
            </div>
            {/* Presence Penalty */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">存在惩罚</h5>
                <p className="text-xs text-on-surface-variant">Presence penalty</p>
                {cfg.presence_penalty === 0.0 && (
                  <span className="text-[10px] font-bold bg-on-surface/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold">{cfg.presence_penalty}</span>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer" max="2" min="-2" step="0.1" type="range" value={cfg.presence_penalty} onChange={handlePresencePenaltyChange}/>
            </div>
            {/* Frequency Penalty */}
            <div className="p-6 rounded-2xl bg-surface-container-lowest shadow-sm space-y-6">
              <div>
                <h5 className="font-bold text-on-surface">频率惩罚</h5>
                <p className="text-xs text-on-surface-variant">Frequency penalty</p>
                {cfg.frequency_penalty === 0.0 && (
                  <span className="text-[10px] font-bold bg-on-surface/10 px-2 py-0.5 rounded-full mt-1 inline-block">推荐设置</span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold">{cfg.frequency_penalty}</span>
              </div>
              <input className="w-full h-1 bg-surface-container-high rounded-full appearance-none cursor-pointer" max="2" min="-2" step="0.1" type="range" value={cfg.frequency_penalty} onChange={handleFrequencyPenaltyChange}/>
            </div>
          </div>
        </section>
      </div>
      {/* Footer Action Panel */}
      <footer className="pt-12">
        <div className="flex flex-col md:flex-row items-center justify-between p-6 rounded-2xl bg-[#006b5f]/5 border border-primary/10">
          <div className="flex items-center space-x-4 mb-4 md:mb-0">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">verified_user</span>
            </div>
            <div>
              <p className="text-sm font-bold text-on-surface">安全协议已激活</p>
              <p className="text-xs text-on-surface-variant">All configuration changes are logged for auditing.</p>
            </div>
          </div>
          <div className="flex space-x-4 w-full md:w-auto">
            <button 
              onClick={load} 
              disabled={loading || saving}
              className="flex-1 md:flex-none px-8 py-3 text-sm font-bold text-on-surface-variant hover:text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined animate-spin">refresh</span>
                  加载中...
                </span>
              ) : '放弃'}
            </button>
            <button 
              onClick={save} 
              disabled={loading || saving}
              className="flex-1 md:flex-none px-10 py-3 bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-xl font-bold shadow-lg shadow-primary/20 active:scale-95 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <span className="flex items-center gap-2">
                  <span className="material-symbols-outlined animate-spin">refresh</span>
                  保存中...
                </span>
              ) : '应用更改'}
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
