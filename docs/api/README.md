# API 接口文档

## 目录
- [基础信息](#基础信息)
- [API 版本](#api-版本)
- [认证方式](#认证方式)
- [状态码说明](#状态码说明)
- [接口详细定义](#接口详细定义)
- [v1 API 接口](#v1-api-接口)
- [示例代码](#示例代码)

---

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **v1 Base URL**: `http://localhost:8000/api/v1`
- **数据格式**: JSON
- **字符编码**: UTF-8

### 交互式文档

启动后端服务后，可以访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API 版本

本系统提供两个版本的 API：

| 版本 | Base URL | 说明 |
|------|----------|------|
| v1 | `/api/v1/*` | 最新版本的 API 接口，推荐使用 |
| 原始 | `/api/*` | 保持向后兼容的原始接口 |

### 版本差异

v1 API 与原始 API 的主要差异：

- v1 API 使用 `/api/v1/` 前缀
- v1 API 结构更清晰，路由分组更合理
- 新功能将首先在 v1 API 中提供

---

## 认证方式

### Bearer Token 认证

部分接口需要认证，使用 JWT (JSON Web Token) 进行认证。

**获取 Token**:
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

**使用 Token**:
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 免认证接口

以下接口不需要认证：
- `POST /api/auth/login`
- `POST /api/auth/register` (如果启用注册)
- `GET /api/auth/registration-config`
- `GET /api/auth/pdf-conversion-config`
- `GET /api/config` (部分配置)
- `GET /api/health`
- `GET /` (根路径)

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 (速率限制) |
| 500 | 服务器内部错误 |

---

## 接口详细定义

### 1. 系统接口

#### 1.1 健康检查

**接口**: `GET /api/health`

**描述**: 检查系统健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": 1704067200.123,
  "version": "2.0",
  "services": {
    "vector_store": {"status": "ok", "doc_count": 100},
    "api_key": {"status": "ok", "access_count": 5000}
  }
}
```

#### 1.2 根路径

**接口**: `GET /`

**响应示例**:
```json
{
  "message": "实验室智能助手 - 后端 API",
  "version": "2.0"
}
```

---

### 2. 认证接口

#### 2.1 用户登录

**接口**: `POST /api/auth/login`

**描述**: 用户登录获取访问令牌

**请求参数** (application/x-www-form-urlencoded):
```
username=your_username&password=your_password
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com",
    "role": "user"
  }
}
```

#### 2.2 用户注册

**接口**: `POST /api/auth/register`

**描述**: 注册新用户（需要启用注册功能）

**请求参数**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string (至少8位)"
}
```

**响应示例**:
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

#### 2.3 获取当前用户信息

**接口**: `GET /api/auth/me`

**需要认证**: 是

**响应示例**:
```json
{
  "id": 1,
  "username": "your_username",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### 3. 文档管理接口

#### 3.1 上传文档

**接口**: `POST /api/upload`

**描述**: 上传文档到知识库

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | File[] | 是 | 要上传的文件列表 |

**支持的文件格式**: PDF, DOCX, DOC, TXT, MD, PPTX, CSV

**响应示例**:
```json
{
  "status": "ok",
  "files": [
    {
      "filename": "document.md",
      "chunks_count": 10,
      "summary_generated": true
    }
  ],
  "failed": [],
  "message": "成功处理 1 个文件，失败 0 个文件"
}
```

#### 3.2 获取文档列表

**接口**: `GET /api/documents`

**描述**: 获取已上传的文档列表

**响应示例**:
```json
{
  "documents": [
    {
      "filename": "document.md",
      "upload_time": "2024-01-01T00:00:00",
      "size": 10240,
      "doc_type": ".md"
    }
  ]
}
```

#### 3.3 删除文档

**接口**: `DELETE /api/documents/{filename}`

**或**: `DELETE /api/documents?file={filename}`

**描述**: 删除指定文档

**响应示例**:
```json
{
  "status": "deleted",
  "file": "document.md"
}
```

#### 3.4 清空知识库

**接口**: `POST /api/clear`

**描述**: 清空所有文档和向量库

**响应示例**:
```json
{
  "status": "cleared"
}
```

---

### 4. 问答接口

#### 4.1 问答（流式）

**接口**: `POST /api/qa`

**描述**: 基于知识库进行问答

**请求参数**:
```json
{
  "question": "string",
  "top_k": 5,
  "provider": "openai",
  "stream": true,
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2048,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "enable_thinking": false,
  "use_react": false,
  "messages": []
}
```

**参数说明**:
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| question | string | - | 用户问题（必填） |
| top_k | integer | 5 | 检索返回的文档数量 |
| provider | string | null | LLM 供应商（openai/ollama） |
| stream | boolean | false | 是否流式输出 |
| temperature | float | null | 生成温度（0-2） |
| top_p | float | null | 核采样参数 |
| max_tokens | integer | null | 最大生成 token 数 |
| presence_penalty | float | null | 存在惩罚 |
| frequency_penalty | float | null | 频率惩罚 |
| enable_thinking | boolean | null | 是否启用思考步骤显示 |
| use_react | boolean | null | 是否启用 ReAct 多步推理模式 |
| messages | array | [] | 对话历史 |

**响应格式**: Server-Sent Events (SSE)

**事件类型**:
- `sources`: 引用来源
- `content`: 回答内容
- `thinking`: 思考步骤（当 enable_thinking 为 true 时）
- `state`: 状态信息
- `[DONE]`: 结束信号

**流式响应示例**:
```
data: {"sources": [{"filename": "doc1.md", "content": "...", "score": 0.95}]}

data: {"content": "根据"}

data: {"content": "文档"}

data: [DONE]
```

---

### 5. 配置管理接口

#### 5.1 获取配置

**接口**: `GET /api/config`

**描述**: 获取当前系统配置

**响应示例**:
```json
{
  "provider": "openai",
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "chunk_size": 1500,
  "temperature": 0.7,
  "top_k": 5,
  "hybrid_search": {
    "enabled": true,
    "bm25_weight": 0.5,
    "embedding_weight": 0.5
  }
}
```

#### 5.2 更新配置

**接口**: `POST /api/config`

**描述**: 更新系统配置

**请求参数**: 任意 config.json 中的配置项

**示例**:
```json
{
  "temperature": 0.8,
  "top_k": 10
}
```

**响应示例**:
```json
{
  "status": "saved",
  "config": {
    "provider": "openai",
    "temperature": 0.8,
    "top_k": 10,
    "...": "..."
  }
}
```

---

### 6. 向量库管理接口

#### 6.1 获取向量库状态

**接口**: `GET /api/vector-store/status`

**描述**: 获取向量库当前状态

**响应示例**:
```json
{
  "count": 100,
  "metadata": {
    "name": "lab_agent_collection",
    "dimension": 512
  }
}
```

#### 6.2 重置向量库

**接口**: `POST /api/vector-store/reset`

**描述**: 重置向量库（删除所有向量）

**响应示例**:
```json
{
  "status": "reset",
  "message": "向量库已重置"
}
```

---

### 7. 嵌入模型管理接口

#### 7.1 获取推荐模型列表

**接口**: `GET /api/embedding/models/recommended`

**描述**: 获取推荐的嵌入模型列表

**响应示例**:
```json
{
  "status": "ok",
  "models": [
    {
      "name": "BAAI/bge-small-zh-v1.5",
      "description": "中文小型嵌入模型",
      "dimensions": 512,
      "language": "zh"
    }
  ]
}
```

#### 7.2 设置嵌入模式

**接口**: `POST /api/embedding/mode`

**描述**: 切换嵌入模式（本地/OpenAI）

**请求参数**:
```json
{
  "mode": "local",
  "reset_collection": false
}
```

**响应示例**:
```json
{
  "status": "ok",
  "message": "已切换到 local 模式",
  "reset_collection": false
}
```

---

## 图结构知识库 API

以下为新增的图结构知识库相关接口。

#### 查看图谱可视化
```
GET /api/graph/view
```
浏览器中直接查看交互式知识图谱 HTML。

#### 生成/刷新可视化
```
GET /api/graph/visualize
```

#### 图统计信息
```
GET /api/graph/stats
```
返回节点数、边数、文档数、实体类型分布。

#### 社区检测
```
GET /api/graph/communities
```
返回图社区检测结果，展示主题聚类。

---

## 示例代码

### Python 示例

#### 使用 requests 库

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def login(username, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]

def upload_document(token, file_path):
    with open(file_path, "rb") as f:
        files = {"files": f}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=headers
        )
        return response.json()

def ask_question_stream(token, question):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/qa",
        json={"question": question, "stream": True},
        headers=headers,
        stream=True
    )

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    break
                try:
                    parsed = json.loads(data)
                    if 'content' in parsed:
                        print(parsed['content'], end='', flush=True)
                except json.JSONDecodeError:
                    pass

def health_check():
    response = requests.get(f"{BASE_URL}/health")
    return response.json()
```

### JavaScript 示例

#### 使用 Axios

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function login(username, password) {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)

  const response = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('files', file)

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function askQuestionStream(question, onData, onComplete) {
  const response = await api.post('/qa', {
    question,
    stream: true
  }, {
    responseType: 'stream'
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      onComplete && onComplete()
      break
    }

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)
          onData && onData(parsed)
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }
}

export async function healthCheck() {
  const response = await api.get('/health')
  return response.data
}

export default api
```

---

## 下一步

- 查看 [后端开发文档](../backend/README.md) 了解接口实现
- 查看 [前端开发文档](../frontend/README.md) 了解前端如何调用 API