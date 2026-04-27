# 前端开发文档

## 目录
- [架构设计](#架构设计)
- [技术栈选型](#技术栈选型)
- [核心功能实现](#核心功能实现)
- [目录结构](#目录结构)
- [配置指南](#配置指南)
- [开发环境搭建](#开发环境搭建)
- [常见问题解决方案](#常见问题解决方案)

---

## 架构设计

### 整体架构

前端采用 Vue 3 + Composition API 的现代化架构：

```
┌─────────────────────────────────────────────────────────┐
│                       应用层 (App Layer)                   │
│                    ┌───────────────┐                      │
│                    │   App.vue     │                      │
│                    └───────────────┘                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   路由层      │   │   状态管理层   │   │   视图层      │
│ (Vue Router)  │   │   (Pinia)     │   │   (Views)     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌───────────────┐
                    │   组件层      │
                    │  (Components) │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   服务层      │
                    │  (Services)   │
                    └───────────────┘
```

### 设计模式

1. **组件化设计**：UI 拆分为可复用组件
2. **状态管理模式**：使用 Pinia 进行全局状态管理
3. **服务层模式**：API 调用集中在 services 层
4. **路由守卫模式**：通过 Vue Router 实现权限控制

---

## 技术栈选型

### 核心框架

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|----------|
| Vue | >= 3.4.0 | 前端框架 | 渐进式框架、Composition API、性能优秀 |
| Vite | >= 5.0.0 | 构建工具 | 极速冷启动、热更新、开发体验极佳 |
| Tailwind CSS | >= 4.2.2 | CSS 框架 | 实用优先、快速开发、易于维护 |
| Pinia | >= 2.1.0 | 状态管理 | Vue 3 官方推荐、简洁、类型安全 |
| Vue Router | >= 4.2.0 | 路由管理 | 官方路由、与 Vue 3 完美配合 |

### 工具库

| 技术 | 版本 | 用途 |
|------|------|------|
| Axios | >= 1.6.0 | HTTP 客户端 |
| Marked | >= 18.0.0 | Markdown 解析 |

### 开发工具

| 技术 | 版本 | 用途 |
|------|------|------|
| @vitejs/plugin-vue | >= 5.0.0 | Vue 插件 |
| @tailwindcss/postcss | >= 4.2.2 | PostCSS 插件 |
| Autoprefixer | >= 10.4.27 | CSS 前缀自动添加 |

---

## 核心功能实现

### 1. 路由管理

```javascript
// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from '../stores/appStore'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/uploads',
    name: 'Uploads',
    component: () => import('../views/UploadsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const appStore = useAppStore()
  const token = localStorage.getItem('auth_token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
```

### 2. 状态管理

```javascript
// frontend/src/stores/appStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAppStore = defineStore('app', () => {
  // 状态
  const user = ref(null)
  const config = ref(null)
  const currentSession = ref(null)
  const messages = ref([])
  const isLoading = ref(false)
  
  // 计算属性
  const isAuthenticated = computed(() => !!user.value)
  
  // 动作
  async function login(credentials) {
    try {
      const response = await api.post('/auth/login', credentials)
      const { access_token } = response.data
      localStorage.setItem('auth_token', access_token)
      await fetchUserInfo()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }
  
  function logout() {
    user.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
  }
  
  async function fetchUserInfo() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem('user_info', JSON.stringify(response.data))
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    }
  }
  
  async function fetchConfig() {
    try {
      const response = await api.get('/config')
      config.value = response.data
    } catch (error) {
      console.error('Failed to fetch config:', error)
    }
  }
  
  async function updateConfig(newConfig) {
    try {
      const response = await api.post('/config', newConfig)
      config.value = response.data.config
      return true
    } catch (error) {
      console.error('Failed to update config:', error)
      return false
    }
  }
  
  async function sendMessage(question, options = {}) {
    isLoading.value = true
    try {
      const response = await api.post('/qa', {
        question,
        stream: true,
        ...options
      }, {
        responseType: 'stream'
      })
      
      return handleStreamResponse(response)
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  function handleStreamResponse(response) {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let sources = []
    let answer = ''
    
    return {
      async *[Symbol.asyncIterator]() {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') continue
              
              try {
                const parsed = JSON.parse(data)
                
                if (parsed.sources) {
                  sources = parsed.sources
                  yield { type: 'sources', data: sources }
                }
                if (parsed.content) {
                  answer += parsed.content
                  yield { type: 'content', data: parsed.content }
                }
                if (parsed.state) {
                  yield { type: 'state', data: parsed.state }
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }
        
        yield { type: 'done', answer, sources }
      }
    }
  }
  
  return {
    // 状态
    user,
    config,
    currentSession,
    messages,
    isLoading,
    // 计算属性
    isAuthenticated,
    // 动作
    login,
    logout,
    fetchUserInfo,
    fetchConfig,
    updateConfig,
    sendMessage
  }
})
```

### 3. API 服务层

```javascript
// frontend/src/services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理认证错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### 4. 聊天组件

```vue
<!-- frontend/src/views/ChatView.vue -->
<template>
  <div class="chat-view h-screen flex flex-col">
    <!-- 消息列表 -->
    <div class="flex-1 overflow-y-auto p-4">
      <div class="max-w-4xl mx-auto space-y-4">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-content">
            <div v-if="message.role === 'user'" class="font-bold mb-1">
              用户
            </div>
            <div v-else class="font-bold mb-1">
              助手
            </div>
            <div v-html="formatMarkdown(message.content)"></div>
            
            <!-- 引用来源 -->
            <div v-if="message.sources && message.sources.length > 0" class="mt-3">
              <div class="text-sm text-gray-600 mb-1">引用来源:</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(source, i) in message.sources"
                  :key="i"
                  class="source-tag"
                  @mouseenter="showSourcePreview(source, $event)"
                  @mouseleave="hideSourcePreview"
                >
                  {{ source.filename }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 加载指示器 -->
        <div v-if="isLoading" class="loading-indicator">
          <div class="spinner"></div>
          <span class="ml-2">正在思考...</span>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="border-t p-4">
      <div class="max-w-4xl mx-auto">
        <form @submit.prevent="handleSubmit" class="flex gap-2">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="输入您的问题..."
            class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
            :disabled="isLoading"
          />
          <button
            type="submit"
            class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            :disabled="isLoading || !inputMessage.trim()"
          >
            发送
          </button>
        </form>
      </div>
    </div>
    
    <!-- 文档预览悬浮卡片 -->
    <CitationHoverCard
      v-if="hoveredSource"
      :source="hoveredSource"
      :position="hoverPosition"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../stores/appStore'
import { marked } from 'marked'
import CitationHoverCard from '../components/gen-ui/CitationHoverCard.vue'

const appStore = useAppStore()
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const hoveredSource = ref(null)
const hoverPosition = ref({ x: 0, y: 0 })

function formatMarkdown(text) {
  return marked(text)
}

async function handleSubmit() {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: question
  })
  
  isLoading.value = true
  
  try {
    const stream = await appStore.sendMessage(question)
    let assistantMessage = {
      role: 'assistant',
      content: '',
      sources: []
    }
    
    messages.value.push(assistantMessage)
    
    for await (const event of stream) {
      if (event.type === 'sources') {
        assistantMessage.sources = event.data
      } else if (event.type === 'content') {
        assistantMessage.content += event.data
      } else if (event.type === 'done') {
        assistantMessage.content = event.answer
        assistantMessage.sources = event.sources
      }
    }
  } catch (error) {
    console.error('Error sending message:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后重试。'
    })
  } finally {
    isLoading.value = false
  }
}

function showSourcePreview(source, event) {
  hoveredSource.value = source
  hoverPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
}

function hideSourcePreview() {
  hoveredSource.value = null
}

onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.chat-view {
  background-color: #f9fafb;
}

.message {
  max-width: 80%;
}

.message.user {
  margin-left: auto;
}

.message.assistant {
  margin-right: auto;
}

.message-content {
  padding: 1rem;
  border-radius: 0.5rem;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
  background-color: #3b82f6;
  color: white;
}

.source-tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background-color: #e5e7eb;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.source-tag:hover {
  background-color: #d1d5db;
}

.loading-indicator {
  display: flex;
  align-items: center;
  padding: 1rem;
  color: #6b7280;
}

.spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

---

## 目录结构

```
frontend/
├── src/
│   ├── main.js                  # 应用入口
│   ├── App.vue                  # 根组件
│   ├── App.jsx                  # React 根组件（备用）
│   ├── main.jsx                 # React 入口（备用）
│   ├── styles.css               # 全局样式
│   ├── components/              # 组件
│   │   ├── Chat.jsx            # 聊天组件
│   │   ├── Settings.jsx        # 设置组件
│   │   ├── Uploads.jsx         # 上传组件
│   │   ├── ErrorBoundary.jsx   # 错误边界
│   │   └── gen-ui/             # 通用 UI 组件
│   │       ├── CitationHoverCard.vue
│   │       ├── ComponentRegistry.js
│   │       ├── DataChart.vue
│   │       ├── DataTable.vue
│   │       ├── DocumentPreviewPanel.vue
│   │       ├── JsonDisplay.vue
│   │       ├── JsonNode.vue
│   │       ├── ReActModePrompt.vue
│   │       ├── ReActThinkingDisplay.vue
│   │       └── ThinkingSteps.vue
│   ├── views/                   # 页面视图
│   │   ├── ChatView.vue        # 聊天页面
│   │   ├── LoginView.vue       # 登录页面
│   │   ├── SettingsView.vue    # 设置页面
│   │   └── UploadsView.vue     # 上传页面
│   ├── router/                  # 路由
│   │   └── index.js
│   ├── services/                # API 服务
│   │   ├── api.js              # API 客户端
│   │   ├── auth.js             # 认证服务
│   │   └── sessions.js         # 会话服务
│   └── stores/                  # Pinia 状态管理
│       ├── index.js
│       └── appStore.js         # 应用状态
├── index.html                   # HTML 模板
├── vite.config.js              # Vite 配置
├── tailwind.config.cjs         # Tailwind CSS 配置
├── postcss.config.cjs          # PostCSS 配置
├── package.json                # npm 依赖
├── package-lock.json
└── test-jsonnode.html          # 测试页面
```

---

## 配置指南

### Vite 配置

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

### Tailwind CSS 配置

```javascript
// frontend/tailwind.config.cjs
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8'
        }
      }
    }
  },
  plugins: []
}
```

### 环境变量

创建 `.env` 文件：

```env
# API 基础 URL（开发环境）
VITE_API_BASE_URL=http://localhost:8000/api

# 生产环境 API 基础 URL
# VITE_API_BASE_URL=https://your-domain.com/api
```

---

## 开发环境搭建

### 系统要求

- Node.js 16+
- npm 7+

### 步骤 1：安装依赖

```bash
cd frontend
npm install
```

### 步骤 2：启动开发服务器

```bash
npm run dev
```

开发服务器将运行在 http://localhost:5175

### 步骤 3：构建生产版本

```bash
npm run build
```

构建产物将输出到 `frontend/dist` 目录

### 步骤 4：预览生产构建

```bash
npm run preview
```

### 开发工具推荐

- **IDE**: VS Code
- **Vue DevTools**: 浏览器扩展
- **ESLint**: 代码检查
- **Prettier**: 代码格式化

---

## 常见问题解决方案

### 1. 前端无法连接后端

**症状**: 前端显示网络错误或无法加载数据

**解决方案**:
1. 确认后端服务正在运行
2. 检查 `vite.config.js` 中的代理配置
3. 确认后端地址和端口正确
4. 检查浏览器控制台的错误信息
5. 检查 CORS 配置

### 2. 依赖安装失败

**症状**: `npm install` 失败

**解决方案**:
1. 清除 npm 缓存：`npm cache clean --force`
2. 删除 `node_modules` 和 `package-lock.json`，重新安装
3. 使用国内镜像源：
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install
   ```
4. 检查 Node.js 版本是否满足要求

### 3. 热更新不工作

**症状**: 修改代码后页面不自动刷新

**解决方案**:
1. 检查是否有编译错误
2. 重启开发服务器
3. 检查文件路径是否正确
4. 清除浏览器缓存

### 4. 认证状态丢失

**症状**: 刷新页面后需要重新登录

**解决方案**:
1. 确认 token 正确存储在 localStorage
2. 检查路由守卫配置
3. 确认 API 请求拦截器正确添加 token
4. 检查 token 过期时间

### 5. 流式响应处理问题

**症状**: 聊天消息不显示或显示不完整

**解决方案**:
1. 检查 `responseType: 'stream'` 是否正确设置
2. 确认 Stream API 使用正确
3. 检查解码逻辑
4. 查看浏览器网络面板的响应内容

---

## 下一步

- 查看 [API 接口文档](../api/README.md) 了解所有可用接口
- 查看 [后端开发文档](../backend/README.md) 了解后端架构
