<template>
  <div class="px-4 md:px-12 py-6 md:py-8 max-w-5xl mx-auto space-y-6 md:space-y-10">
    <div class="space-y-2">
      <!-- <h1 class="text-2xl md:text-4xl font-black text-on-surface tracking-tight">系统设置</h1> -->
      <div class="flex items-center gap-3 md:gap-4 flex-wrap">
        <div class="px-3 py-1 rounded-full bg-secondary-container text-on-secondary-container text-[10px] font-bold uppercase tracking-widest">v2.4.0-Stable</div>
        <!-- 调试信息 -->
        <div class="px-3 py-1 rounded-full bg-tertiary-container text-on-tertiary-container text-[10px] font-bold">
          用户角色: {{ currentUserRole }}
        </div>
        <div class="px-3 py-1 rounded-full text-[10px] font-bold" :class="isAdmin ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
          管理员权限: {{ isAdmin ? '是' : '否' }}
        </div>
      </div>
    </div>

    <div v-if="error" class="bg-error/10 border border-error/20 rounded-xl p-4 flex items-start gap-3">
      <span class="material-symbols-outlined text-error">error</span>
      <div>
        <p class="font-bold text-error">配置错误</p>
        <p class="text-sm text-error/80">{{ error }}</p>
      </div>
    </div>

    <!-- 大语言模型引擎供应商 -->
    <section class="space-y-4 md:space-y-6">
      <!-- <h2 class="text-2xl md:text-3xl font-black text-on-surface tracking-tight">
        大语言模型引擎
        <span class="text-primary">供应商</span>
      </h2> -->
      
      <div class="space-y-3 md:space-y-4">
        <!-- OpenAI -->
        <div 
          @click="selectProvider('openai')"
          class="p-4 md:p-8 rounded-xl md:rounded-2xl cursor-pointer transition-all border-2"
          :class="cfg.provider === 'openai' 
            ? 'border-primary bg-primary/5 shadow-lg' 
            : 'border-outline-variant/20 bg-surface hover:border-outline-variant hover:bg-surface-container'"
        >
          <div class="flex items-start justify-between">
            <div class="space-y-3 md:space-y-4">
              <div class="w-12 h-12 md:w-16 md:h-16 bg-surface-container rounded-lg flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl md:text-4xl" :class="cfg.provider === 'openai' ? 'text-primary' : 'text-outline'">hub</span>
              </div>
              <div>
                <h3 class="text-xl md:text-2xl font-black text-on-surface">OpenAI 云端</h3>
                <p class="text-sm md:text-lg text-on-surface-variant mt-2">Enterprise-grade performance. Required for complex reasoning and large-scale analysis.</p>
              </div>
            </div>
            <div class="w-5 h-5 md:w-6 md:h-6 rounded-full border-2 flex items-center justify-center"
              :class="cfg.provider === 'openai' ? 'border-primary bg-primary' : 'border-outline'">
              <div v-if="cfg.provider === 'openai'" class="w-2 h-2 md:w-3 md:h-3 bg-white rounded-full"></div>
            </div>
          </div>
        </div>

        <!-- DeepSeek -->
        <div
          @click="selectProvider('deepseek')"
          class="p-4 md:p-8 rounded-xl md:rounded-2xl cursor-pointer transition-all border-2"
          :class="cfg.provider === 'deepseek'
            ? 'border-primary bg-primary/5 shadow-lg'
            : 'border-outline-variant/20 bg-surface hover:border-outline-variant hover:bg-surface-container'"
        >
          <div class="flex items-start justify-between">
            <div class="space-y-3 md:space-y-4">
              <div class="w-12 h-12 md:w-16 md:h-16 bg-surface-container rounded-lg flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl md:text-4xl" :class="cfg.provider === 'deepseek' ? 'text-primary' : 'text-outline'">neurology</span>
              </div>
              <div>
                <h3 class="text-xl md:text-2xl font-black text-on-surface">DeepSeek 云端</h3>
                <p class="text-sm md:text-lg text-on-surface-variant mt-2">Advanced reasoning with DeepSeek's latest models. Supports chain-of-thought thinking with reasoning preview.</p>
              </div>
            </div>
            <div class="w-5 h-5 md:w-6 md:h-6 rounded-full border-2 flex items-center justify-center"
              :class="cfg.provider === 'deepseek' ? 'border-primary bg-primary' : 'border-outline'">
              <div v-if="cfg.provider === 'deepseek'" class="w-2 h-2 md:w-3 md:h-3 bg-white rounded-full"></div>
            </div>
          </div>
        </div>

        <!-- Ollama -->
        <div 
          @click="selectProvider('ollama')"
          class="p-4 md:p-8 rounded-xl md:rounded-2xl cursor-pointer transition-all border-2"
          :class="cfg.provider === 'ollama' 
            ? 'border-primary bg-primary/5 shadow-lg' 
            : 'border-outline-variant/20 bg-surface hover:border-outline-variant hover:bg-surface-container'"
        >
          <div class="flex items-start justify-between">
            <div class="space-y-3 md:space-y-4">
              <div class="w-12 h-12 md:w-16 md:h-16 bg-surface-container rounded-lg flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl md:text-4xl" :class="cfg.provider === 'ollama' ? 'text-primary' : 'text-outline'">memory</span>
              </div>
              <div>
                <h3 class="text-xl md:text-2xl font-black text-on-surface">Ollama 本地</h3>
                <p class="text-sm md:text-lg text-on-surface-variant mt-2">On-premise execution. Ideal for sensitive data compliance and air-gapped environments.</p>
              </div>
            </div>
            <div class="w-5 h-5 md:w-6 md:h-6 rounded-full border-2 flex items-center justify-center"
              :class="cfg.provider === 'ollama' ? 'border-primary bg-primary' : 'border-outline'">
              <div v-if="cfg.provider === 'ollama'" class="w-2 h-2 md:w-3 md:h-3 bg-white rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- API凭证 -->
    <section class="space-y-4 md:space-y-6">
      <!-- <h2 class="text-2xl md:text-3xl font-black text-on-surface tracking-tight">API 凭证</h2> -->
      
      <div class="space-y-4 md:space-y-6">
        <!-- OpenAI API配置提示 -->
        <div v-if="cfg.provider === 'openai'" class="space-y-3">
          <div class="bg-info/10 border border-info/20 rounded-xl p-4 space-y-3">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-info">info</span>
              <div>
                <h4 class="font-bold text-info">API 凭证配置</h4>
                <p class="text-sm text-info/80 mt-1">
                  为安全起见，API 凭证现在通过环境变量配置。请在项目根目录创建 <code class="bg-surface-container px-1 py-0.5 rounded">.env</code> 文件，并设置以下环境变量：
                </p>
                <div class="mt-3 p-3 bg-surface-container rounded-lg font-mono text-sm">
                  <p>OPENAI_API_KEY=your-api-key-here</p>
                  <p>OPENAI_BASE_URL=https://api.openai.com/v1</p>
                </div>
                <p class="text-sm text-info/80 mt-3">
                  修改 <code class="bg-surface-container px-1 py-0.5 rounded">.env</code> 文件后，需要重启后端服务以生效。
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型选择 -->
        <div v-if="cfg.provider === 'openai'" class="space-y-3">
          <label class="text-sm font-bold text-on-surface-variant uppercase tracking-wide">模型</label>
          <select 
            v-model="cfg.openai_chat_model"
            @change="handleModelChange"
            class="w-full bg-surface-container-high rounded-xl px-4 md:px-6 py-4 md:py-5 text-on-surface font-medium focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm md:text-base"
          >
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4-turbo">GPT-4 Turbo</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-5-nano">GPT-5-nano</option>
            <option value="gpt-5">GPT-5</option>
          </select>
        </div>

        <!-- DeepSeek API配置提示 -->
        <div v-if="cfg.provider === 'deepseek'" class="space-y-3">
          <div class="bg-info/10 border border-info/20 rounded-xl p-4 space-y-3">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-info">info</span>
              <div>
                <h4 class="font-bold text-info">DeepSeek API 配置</h4>
                <p class="text-sm text-info/80 mt-1">
                  请在项目根目录的 <code class="bg-surface-container px-1 py-0.5 rounded">.env</code> 文件中设置以下环境变量：
                </p>
                <div class="mt-3 p-3 bg-surface-container rounded-lg font-mono text-sm">
                  <p>DEEPSEEK_API_KEY=sk-your-deepseek-api-key</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- DeepSeek 模型选择 -->
        <div v-if="cfg.provider === 'deepseek'" class="space-y-3">
          <label class="text-sm font-bold text-on-surface-variant uppercase tracking-wide">模型</label>
          <select
            v-model="cfg.deepseek_chat_model"
            @change="handleModelChange"
            class="w-full bg-surface-container-high rounded-xl px-4 md:px-6 py-4 md:py-5 text-on-surface font-medium focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm md:text-base"
          >
            <option value="deepseek-v4-flash">deepseek-v4-flash</option>
            <option value="deepseek-v4-pro">deepseek-v4-pro</option>
          </select>
          <p class="text-xs text-on-surface-variant mt-1">启用 Thinking 后自动使用 DeepSeek Reasoner 模型获取思考链预览。</p>
        </div>

        <!-- Ollama URL -->
        <div v-if="cfg.provider === 'ollama'" class="space-y-3">
          <label class="text-sm font-bold text-on-surface-variant uppercase tracking-wide">Ollama URL</label>
          <input 
            v-model="cfg.ollama_url"
            @input="handleOllamaUrlChange"
            placeholder="http://localhost:11434"
            class="w-full bg-surface-container-high rounded-xl px-4 md:px-6 py-4 md:py-5 text-on-surface font-mono placeholder:text-outline/50 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm md:text-base"
          />
        </div>

        <!-- Ollama 模型 -->
        <div v-if="cfg.provider === 'ollama'" class="space-y-3">
          <label class="text-sm font-bold text-on-surface-variant uppercase tracking-wide">模型</label>
          <select 
            v-model="cfg.ollama_model"
            @input="handleOllamaModelChange"
            placeholder="llama2"
            class="w-full bg-surface-container-high rounded-xl px-4 md:px-6 py-4 md:py-5 text-on-surface font-mono placeholder:text-outline/50 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm md:text-base"
          >
            <option value="qwen3:4b-instruct">Qwen3:4b-instruct</option>
            <option value="Qwen3:4B">Qwen3:4B</option>
          </select>
        </div>
      </div>
    </section>

    <!-- 用户注册配置（仅管理员可见） -->
    <div class="flex gap-4 md:gap-6">
  <!-- 用户注册配置 -->
  <section v-if="isAdmin" class="w-1/2">
    <div class="bg-surface-container-low rounded-xl md:rounded-2xl p-4 md:p-6 space-y-4 h-full flex flex-col">
      <div class="flex-grow">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-bold text-on-surface text-lg">允许用户注册</h3>
            <p class="text-sm text-on-surface-variant mt-1">启用后，新用户可以通过登录页面注册账号</p>
          </div>
          <button
            @click="allowUserRegistration = !allowUserRegistration"
            :disabled="registrationConfigLoading"
            class="relative w-16 h-8 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-primary/30 flex-shrink-0"
            :class="allowUserRegistration ? 'bg-primary' : 'bg-outline-variant'"
          >
            <div
              class="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow transition-transform duration-300"
              :class="allowUserRegistration ? 'translate-x-8' : 'translate-x-0'"
            />
          </button>
        </div>
      </div>
      
      <div class="pt-4 border-t border-outline-variant/20">
        <button
          @click="updateRegistrationConfig"
          :disabled="registrationConfigLoading"
          class="w-full py-3 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span v-if="registrationConfigLoading" class="material-symbols-outlined animate-spin">progress_activity</span>
          {{ registrationConfigLoading ? '更新中...' : '保存注册配置' }}
        </button>
      </div>
    </div>
  </section>

  <!-- PDF 转换配置 -->
  <section v-if="isAdmin" class="w-1/2">
    <div class="bg-surface-container-low rounded-xl md:rounded-2xl p-4 md:p-6 space-y-4 h-full flex flex-col">
      <div class="flex-grow">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-bold text-on-surface text-lg">允许 PDF 转换</h3>
            <p class="text-sm text-on-surface-variant mt-1">启用后，用户可以上传并转换 PDF 文件为 Markdown</p>
          </div>
          <button
            @click="allowPdfConversion = !allowPdfConversion"
            :disabled="pdfConversionConfigLoading"
            class="relative w-16 h-8 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-primary/30 flex-shrink-0"
            :class="allowPdfConversion ? 'bg-primary' : 'bg-outline-variant'"
          >
            <div
              class="absolute top-1 left-1 w-6 h-6 bg-white rounded-full shadow transition-transform duration-300"
              :class="allowPdfConversion ? 'translate-x-8' : 'translate-x-0'"
            />
          </button>
        </div>
      </div>
      
      <div class="pt-4 border-t border-outline-variant/20">
        <button
          @click="updatePdfConversionConfig"
          :disabled="pdfConversionConfigLoading"
          class="w-full py-3 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span v-if="pdfConversionConfigLoading" class="material-symbols-outlined animate-spin">progress_activity</span>
          {{ pdfConversionConfigLoading ? '更新中...' : '保存 PDF 转换配置' }}
        </button>
      </div>
    </div>
  </section>
</div>

    <!-- 保存按钮 -->
    <div class="pt-6 md:pt-8">
      <button 
        @click="save"
        :disabled="saving || loading"
        class="w-full py-3 md:py-4 bg-primary text-on-primary rounded-xl font-black text-base md:text-lg shadow-lg shadow-primary/20 hover:bg-primary/90 active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2 md:gap-3"
      >
        <span v-if="saving" class="material-symbols-outlined animate-spin text-base md:text-xl">progress_activity</span>
        {{ saving ? '保存中...' : loading ? '加载中...' : '应用更改' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watchEffect } from 'vue'
import api from '../services/api'
import { authService } from '../services/auth'

const loading = ref(true)
const saving = ref(false)
const showPassword = ref(false)
const error = ref('')
const isAdmin = ref(false)
const allowUserRegistration = ref(false)
const registrationConfigLoading = ref(false)
const allowPdfConversion = ref(false)
const pdfConversionConfigLoading = ref(false)

const currentUserRole = computed(() => {
  const userInfo = authService.getUserInfo()
  return userInfo?.role || '未知'
})

const cfg = ref({
  provider: 'openai',
  openai_api_key: '',
  openai_base_url: 'https://api.openai-hk.com/v1',
  openai_chat_model: 'gpt-3.5-turbo',
  deepseek_base_url: 'https://api.deepseek.com/v1',
  deepseek_chat_model: 'deepseek-v4-pro',
  deepseek_reasoner_model: 'deepseek-v4-pro',
  ollama_url: 'http://localhost:11434',
  ollama_model: 'qwen3:4b-instruct'
})

const validate = () => {
  if (cfg.value.provider === 'ollama') {
    if (!cfg.value.ollama_url?.trim()) {
      error.value = '请输入 Ollama URL'
      return false
    }
    if (!cfg.value.ollama_model?.trim()) {
      error.value = '请输入 Ollama 模型名称'
      return false
    }
  }
  error.value = ''
  return true
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await api.get('/config')
    if (res.data) {
      cfg.value = { ...cfg.value, ...res.data }
    }
  } catch (e) {
    console.error('Failed to load config:', e)
  } finally {
    loading.value = false
  }
}

const save = async () => {
  if (!validate()) return
  saving.value = true
  try {
    await api.post('/config', cfg.value)
    error.value = ''
    alert('配置保存成功！')
  } catch (e) {
    console.error('Failed to save config:', e)
    const errorMsg = e.response?.data?.detail || e.message || '保存失败'
    error.value = `保存失败: ${errorMsg}`
  } finally {
    saving.value = false
  }
}

// 处理函数
const selectProvider = (provider) => {
  cfg.value.provider = provider
}

const handleApiKeyChange = () => {
  // 自动保存
}

const handleBaseUrlChange = () => {
  // 自动保存
}

const handleModelChange = () => {
  // 自动保存
}

const handleOllamaUrlChange = () => {
  // 自动保存
}

const handleOllamaModelChange = () => {
  // 自动保存
}

const loadCurrentUser = async () => {
  try {
    console.log('[DEBUG] Fetching current user from backend...')
    const user = await authService.getCurrentUser()
    console.log('[DEBUG] Current user from backend:', user)
    
    // 更新 localStorage 中的用户信息
    localStorage.setItem('user_info', JSON.stringify(user))
    
    isAdmin.value = user?.role?.toLowerCase() === 'admin'
    console.log('[DEBUG] Is admin (from backend):', isAdmin.value)
  } catch (e) {
    console.error('[DEBUG] Failed to fetch current user:', e)
    // 降级使用 localStorage
    const userInfo = authService.getUserInfo()
    console.log('[DEBUG] Using user info from localStorage:', userInfo)
    isAdmin.value = userInfo?.role?.toLowerCase() === 'admin'
  }
}

const loadRegistrationConfig = async () => {
  try {
    // 先获取最新的用户信息
    await loadCurrentUser()
    
    if (isAdmin.value) {
      const config = await authService.getRegistrationConfig()
      allowUserRegistration.value = config.allow_user_registration
    }
  } catch (e) {
    console.error('Failed to load registration config:', e)
  }
}

const updateRegistrationConfig = async () => {
  try {
    registrationConfigLoading.value = true
    await authService.updateRegistrationConfig(allowUserRegistration.value)
    alert('注册配置更新成功！')
  } catch (e) {
    console.error('Failed to update registration config:', e)
    const errorMsg = e.response?.data?.detail || e.message || '更新失败'
    alert(`更新失败: ${errorMsg}`)
  } finally {
    registrationConfigLoading.value = false
  }
}

const loadPdfConversionConfig = async () => {
  try {
    if (isAdmin.value) {
      const config = await authService.getPdfConversionConfig()
      allowPdfConversion.value = config.allow_pdf_conversion
    }
  } catch (e) {
    console.error('Failed to load PDF conversion config:', e)
  }
}

const updatePdfConversionConfig = async () => {
  try {
    pdfConversionConfigLoading.value = true
    await authService.updatePdfConversionConfig(allowPdfConversion.value)
    alert('PDF 转换配置更新成功！')
  } catch (e) {
    console.error('Failed to update PDF conversion config:', e)
    const errorMsg = e.response?.data?.detail || e.message || '更新失败'
    alert(`更新失败: ${errorMsg}`)
  } finally {
    pdfConversionConfigLoading.value = false
  }
}

// 动态监测用户信息变化
watchEffect(() => {
  const userInfo = authService.getUserInfo()
  isAdmin.value = userInfo?.role?.toLowerCase() === 'admin'
})

onMounted(() => {
  load()
  loadRegistrationConfig()
  loadPdfConversionConfig()
})
</script>
