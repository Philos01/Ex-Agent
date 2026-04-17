# API 接口文档

## 目录
- [基础信息](#基础信息)
- [认证方式](#认证方式)
- [状态码说明](#状态码说明)
- [接口详细定义](#接口详细定义)
- [示例代码](#示例代码)

---

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **数据格式**: JSON
- **字符编码**: UTF-8

### 交互式文档

启动后端服务后，可以访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

---

## 接口详细定义

### 1. 认证接口

#### 1.1 用户注册

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

---

#### 1.2 用户登录

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

---

#### 1.3 获取当前用户信息

**接口**: `GET /api/auth/me`

**描述**: 获取当前登录用户的信息

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

#### 1.4 获取注册配置

**接口**: `GET /api/auth/registration-config`

**描述**: 获取用户注册功能配置

**响应示例**:
```json
{
  "allow_user_registration": false
}
```

---

#### 1.5 更新注册配置

**接口**: `PUT /api/auth/registration-config`

**描述**: 更新用户注册配置（仅管理员）

**需要认证**: 是（需要管理员权限）

**请求参数**:
```json
{
  "allow_registration": true
}
```

**响应示例**:
```json
{
  "message": "Registration configuration updated successfully",
  "allow_user_registration": true
}
```

---

#### 1.6 获取 PDF 转换配置

**接口**: `GET /api/auth/pdf-conversion-config`

**描述**: 获取 PDF 转换功能配置

**响应示例**:
```json
{
  "allow_pdf_conversion": false
}
```

---

#### 1.7 更新 PDF 转换配置

**接口**: `PUT /api/auth/pdf-conversion-config`

**描述**: 更新 PDF 转换配置（仅管理员）

**需要认证**: 是（需要管理员权限）

**请求参数**:
```json
{
  "allow_pdf_conversion": true
}
```

**响应示例**:
```json
{
  "message": "PDF conversion configuration updated successfully",
  "allow_pdf_conversion": true
}
```

---

### 2. 文档管理接口

#### 2.1 上传文档

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

---

#### 2.2 获取文档列表

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

---

#### 2.3 删除文档

**接口**: `DELETE /api/documents/{filename}`

**或**: `DELETE /api/documents?file={filename}`

**描述**: 删除指定文档

**路径/查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 要删除的文件名 |

**响应示例**:
```json
{
  "status": "deleted",
  "file": "document.md"
}
```

---

#### 2.4 清空知识库

**接口**: `POST /api/clear`

**描述**: 清空所有文档和向量库

**响应示例**:
```json
{
  "status": "cleared"
}
```

---

#### 2.5 获取文档预览

**接口**: `GET /api/document/preview`

**描述**: 获取文档预览内容

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 文档文件名 |
| chunk_index | integer | 否 | 指定 chunk 索引 |

**响应示例**:
```json
{
  "status": "ok",
  "filename": "document.md",
  "full_text": "文档全文内容...",
  "chunk_content": "指定 chunk 内容...",
  "chunk_index": 0
}
```

---

### 3. 问答接口

#### 3.1 问答（流式）

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
- `state`: 状态信息
- `[DONE]`: 结束信号

**流式响应示例**:
```
data: {"sources": [{"filename": "doc1.md", "content": "...", "score": 0.95}]}

data: {"content": "根据"}

data: {"content": "文档"}

data: {"content": "，"}

data: {"content": "这是"}

data: {"content": "回答"}

data: [DONE]
```

---

### 4. 配置管理接口

#### 4.1 获取配置

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

---

#### 4.2 更新配置

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

### 5. 向量库管理接口

#### 5.1 获取向量库状态

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

---

#### 5.2 重置向量库

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

### 6. 嵌入模型管理接口

#### 6.1 获取推荐模型列表

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
    },
    {
      "name": "BAAI/bge-large-zh-v1.5",
      "description": "中文大型嵌入模型",
      "dimensions": 1024,
      "language": "zh"
    }
  ]
}
```

---

#### 6.2 获取嵌入状态

**接口**: `GET /api/embedding/status`

**描述**: 获取当前嵌入模型状态

**响应示例**:
```json
{
  "status": "ok",
  "data": {
    "mode": "local",
    "config": {
      "local_embedding_model": "BAAI/bge-small-zh-v1.5",
      "openai_embedding_model": "text-embedding-3-small"
    },
    "initialized": true,
    "current_mode": "local",
    "local_model": "BAAI/bge-small-zh-v1.5"
  }
}
```

---

#### 6.3 设置嵌入模式

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

#### 6.4 设置本地嵌入模型

**接口**: `POST /api/embedding/local-model`

**描述**: 设置本地嵌入模型

**请求参数**:
```json
{
  "model_name": "BAAI/bge-small-zh-v1.5",
  "cache_dir": ""
}
```

**响应示例**:
```json
{
  "status": "ok",
  "message": "本地模型已设置为: BAAI/bge-small-zh-v1.5",
  "model_name": "BAAI/bge-small-zh-v1.5"
}
```

---

### 7. 摘要管理接口

#### 7.1 列出所有摘要

**接口**: `GET /api/summaries`

**描述**: 列出所有文档摘要

**响应示例**:
```json
{
  "status": "ok",
  "summaries": [
    {
      "filename": "document.md",
      "summary": "文档摘要...",
      "key_topics": ["主题1", "主题2"],
      "quality_score": 0.9,
      "generated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

---

#### 7.2 获取指定文档摘要

**接口**: `GET /api/summaries/{filename}`

**描述**: 获取指定文档的摘要

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 文档文件名 |

**响应示例**:
```json
{
  "status": "ok",
  "summary": {
    "filename": "document.md",
    "summary": "文档摘要...",
    "key_topics": ["主题1", "主题2"],
    "quality_score": 0.9,
    "generated_at": "2024-01-01T00:00:00"
  }
}
```

---

#### 7.3 重新生成摘要

**接口**: `POST /api/summaries/{filename}/regenerate`

**描述**: 重新生成指定文档的摘要

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 文档文件名 |

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| provider | string | 否 | LLM 供应商 |

**响应示例**:
```json
{
  "status": "ok",
  "message": "摘要重新生成成功",
  "summary": { ... }
}
```

---

### 8. 上下文管理接口

#### 8.1 获取上下文历史

**接口**: `GET /api/context/{session_id}`

**描述**: 获取指定会话的上下文历史

**路径参数**:
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| session_id | string | "default" | 会话 ID |

**响应示例**:
```json
{
  "status": "ok",
  "history": [
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "回答1"}
  ],
  "stats": {
    "total_messages": 10,
    "user_messages": 5,
    "assistant_messages": 5
  }
}
```

---

#### 8.2 清除上下文历史

**接口**: `DELETE /api/context/{session_id}`

**描述**: 清除指定会话的上下文历史

**路径参数**:
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| session_id | string | "default" | 会话 ID |

**响应示例**:
```json
{
  "status": "ok",
  "message": "会话 default 的上下文历史已清除"
}
```

---

## 示例代码

### Python 示例

#### 使用 requests 库

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 登录
def login(username, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]

# 上传文档
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

# 问答（非流式）
def ask_question(token, question):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/qa",
        json={"question": question, "stream": False},
        headers=headers
    )
    return response.json()

# 问答（流式）
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
```

### JavaScript 示例

#### 使用 Axios

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 600000
})

// 添加认证拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 登录
export async function login(username, password) {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  
  const response = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

// 上传文档
export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('files', file)
  
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

// 问答（流式）
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

export default api
```

---

## 下一步

- 查看 [后端开发文档](../backend/README.md) 了解接口实现
- 查看 [前端开发文档](../frontend/README.md) 了解前端如何调用 API
