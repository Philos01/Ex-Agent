<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-surface to-surface-container">
    <div class="w-full max-w-md bg-surface rounded-2xl shadow-2xl p-8 space-y-8">
      <!-- 标题 -->
      <div class="text-center space-y-2">
        <h1 class="text-3xl font-black text-on-surface">实验室 Agent</h1>
        <p class="text-on-surface-variant">{{ isLogin ? '请登录以继续' : '创建新账户' }}</p>
      </div>
      
      <!-- 登录/注册表单 -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- 用户名 -->
        <div class="space-y-2">
          <label class="block text-sm font-semibold text-on-surface">用户名</label>
          <input 
            v-model="form.username"
            type="text"
            class="w-full bg-surface-container-high rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="请输入用户名"
            required
          />
        </div>
        
        <!-- 邮箱（仅注册） -->
        <div v-if="!isLogin" class="space-y-2">
          <label class="block text-sm font-semibold text-on-surface">邮箱</label>
          <input 
            v-model="form.email"
            type="email"
            class="w-full bg-surface-container-high rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="请输入邮箱"
            required
          />
        </div>
        
        <!-- 密码 -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-sm font-semibold text-on-surface">密码</label>
            <a v-if="isLogin" href="#" class="text-sm text-primary hover:underline">忘记密码？</a>
          </div>
          <input 
            v-model="form.password"
            type="password"
            class="w-full bg-surface-container-high rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            :placeholder="isLogin ? '请输入密码' : '请输入密码（至少8位）'"
            required
          />
        </div>
        
        <!-- 确认密码（仅注册） -->
        <div v-if="!isLogin" class="space-y-2">
          <label class="block text-sm font-semibold text-on-surface">确认密码</label>
          <input 
            v-model="form.confirmPassword"
            type="password"
            class="w-full bg-surface-container-high rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="请再次输入密码"
            required
          />
        </div>
        
        <!-- 错误信息 -->
        <div v-if="error" class="text-error text-sm text-center">
          {{ error }}
        </div>
        
        <!-- 提交按钮 -->
        <button 
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span v-if="loading" class="material-symbols-outlined animate-spin">progress_activity</span>
          {{ loading ? (isLogin ? '登录中...' : '注册中...') : (isLogin ? '登录' : '注册') }}
        </button>
        
        <!-- 切换登录/注册 -->
        <div class="text-center">
          <span class="text-on-surface-variant">
            {{ isLogin ? '还没有账号？' : '已有账号？' }}
          </span>
          <button 
            type="button"
            @click="toggleMode"
            class="text-primary font-semibold hover:underline ml-1"
          >
            {{ isLogin ? '立即注册' : '立即登录' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/auth'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)
const error = ref('')

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

function toggleMode() {
  isLogin.value = !isLogin.value
  error.value = ''
  form.value = {
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  }
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  
  try {
    if (isLogin.value) {
      await handleLogin()
    } else {
      await handleRegister()
    }
  } catch (err) {
    console.error('Auth error:', err)
    error.value = err.response?.data?.detail || '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  await authService.login(form.value.username, form.value.password)
  router.push('/chat')
}

async function handleRegister() {
  if (form.value.password !== form.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  if (form.value.password.length < 8) {
    error.value = '密码至少需要8位'
    return
  }
  
  await authService.register(form.value.username, form.value.email, form.value.password)
  await authService.login(form.value.username, form.value.password)
  router.push('/chat')
}
</script>
