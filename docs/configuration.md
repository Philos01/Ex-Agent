# 配置指南

本指南详细介绍实验室智能助手的所有配置项。

## 配置文件

项目使用统一的配置文件结构：

1. **config.json** - 主配置文件（JSON 格式，位于项目根目录）
2. **环境变量** - 敏感信息和系统配置

### 配置加载优先级

配置加载优先级从高到低：

1. **环境变量** - 最高优先级，用于敏感信息和覆盖配置
2. **config.json** - 主配置文件（项目根目录），包含所有配置项
3. **DEFAULT_CONFIG** - 后端代码中的默认值（仅作为后备）

**重要**: 所有配置项都应在 `config.json` 中设置，`DEFAULT_CONFIG` 仅作为后备。

---

## config.json 配置

### 完整配置示例

```json
{
  "provider": "openai",
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "local_model_cache_dir": "",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_embedding_model": "text-embedding-3-small",
  "openai_chat_model": "gpt-3.5-turbo",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "qwen3:4b-instruct",
  "chunk_size": 1500,
  "chunk_overlap": 100,
  "temperature": 0.7,
  "top_k": 5,
  "top_p": 0.9,
  "max_tokens": 2048,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "max_history": 10,
  "upload_max_size": 104857600,
  "enable_thinking": false,
  "allow_user_registration": false,
  "pdf_conversion_method": "marker",
  "allow_pdf_conversion": false,
  "hybrid_search": {
    "enabled": true,
    "initial_retrieve_count": 20,
    "final_select_count": 3,
    "bm25_weight": 0.5,
    "embedding_weight": 0.5,
    "rerank_model": "BAAI/bge-reranker-v2-m3",
    "enable_query_rewrite": true
  },
  "summary_search": {
    "enabled": true,
    "relevance_threshold": 0.6,
    "summary_top_k": 5,
    "content_top_k": 3,
    "auto_generate_summary": true
  },
  "context_management": {
    "enabled": true,
    "max_history_rounds": 5,
    "exclude_error_messages": true,
    "exclude_questionable_messages": false
  },
  "timeouts": {
    "enabled": true,
    "requests_post": 60,
    "requests_stream": 60,
    "document_summary": 300,
    "skill_executor_python": 60,
    "skill_executor_shell": 60,
    "react_agent_subprocess": 60,
    "docx2markdown_subprocess": 300
  },
  "skills": {
    "enabled": true,
    "auto_discover": true,
    "arxiv-watcher": {
      "enabled": true,
      "version": "1.0.0"
    },
    "amap-weather": {
      "enabled": true,
      "version": "1.0.0"
    },
    "arxiv_search": {
      "enabled": true,
      "max_results": 5
    }
  }
}
```

---

## 技能系统配置

技能系统配置统一在 `config.json` 的 `skills` 部分管理：

```json
{
  "skills": {
    "enabled": true,
    "auto_discover": true,
    "arxiv-watcher": {
      "enabled": true,
      "version": "1.0.0"
    },
    "amap-weather": {
      "enabled": true,
      "version": "1.0.0"
    },
    "arxiv_search": {
      "enabled": true,
      "max_results": 5
    }
  }
}
```

**说明**:
- `skills.enabled`: 是否启用技能系统
- `skills.auto_discover`: 是否自动发现技能目录中的技能
- `skills.{skill_name}`: 各技能的独立配置
- 技能特定配置（如 API Key）仍需通过环境变量设置

---

## 配置项详解

### 基础配置

#### provider

- **类型**: string
- **默认值**: "openai"
- **可选值**: "openai", "ollama"
- **说明**: LLM 供应商选择

**示例**:
```json
{
  "provider": "ollama"
}
```

---

#### embedding_mode

- **类型**: string
- **默认值**: "local"
- **可选值**: "local", "openai"
- **说明**: 嵌入模型模式

**示例**:
```json
{
  "embedding_mode": "openai"
}
```

---

#### local_embedding_model

- **类型**: string
- **默认值**: "BAAI/bge-small-zh-v1.5"
- **说明**: 本地嵌入模型名称（Hugging Face 模型 ID）

**推荐模型**:
- `BAAI/bge-small-zh-v1.5` - 中文小型模型（推荐）
- `BAAI/bge-base-zh-v1.5` - 中文中型模型
- `BAAI/bge-large-zh-v1.5` - 中文大型模型
- `shibing624/text2vec-base-chinese` - 中文通用模型

**示例**:
```json
{
  "local_embedding_model": "BAAI/bge-large-zh-v1.5"
}
```

---

#### local_model_cache_dir

- **类型**: string
- **默认值**: ""
- **说明**: 本地模型缓存目录，留空使用默认目录

**示例**:
```json
{
  "local_model_cache_dir": "/path/to/models"
}
```

---

### OpenAI 配置

#### openai_base_url

- **类型**: string
- **默认值**: "https://api.openai.com/v1"
- **说明**: OpenAI API 基础 URL

**示例**（使用第三方 API）:
```json
{
  "openai_base_url": "https://api.example.com/v1"
}
```

---

#### openai_embedding_model

- **类型**: string
- **默认值**: "text-embedding-3-small"
- **说明**: OpenAI 嵌入模型

**可选值**:
- `text-embedding-3-small`
- `text-embedding-3-large`
- `text-embedding-ada-002`

---

#### openai_chat_model

- **类型**: string
- **默认值**: "gpt-3.5-turbo"
- **说明**: OpenAI 聊天模型

**可选值**:
- `gpt-3.5-turbo`
- `gpt-4`
- `gpt-4-turbo-preview`
- 其他兼容模型

---

### Ollama 配置

#### ollama_url

- **类型**: string
- **默认值**: "http://localhost:11434"
- **说明**: Ollama 服务地址

---

#### ollama_model

- **类型**: string
- **默认值**: ""
- **说明**: Ollama 模型名称

**常用模型**:
- `llama2`
- `mistral`
- `qwen`（通义千问）
- `qwen3:4b-instruct`
- `yi`（零一万物）

**示例**:
```json
{
  "provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "qwen3:4b-instruct"
}
```

---

### DeepSeek 配置

#### deepseek_api_key

- **类型**: string
- **默认值**: ""
- **说明**: DeepSeek API 密钥。用于调用 DeepSeek 模型。

#### deepseek_base_url

- **类型**: string
- **默认值**: "https://api.deepseek.com/v1"
- **说明**: DeepSeek API 服务地址。

#### deepseek_chat_model

- **类型**: string
- **默认值**: "deepseek-chat"
- **说明**: DeepSeek 对话模型名称。

#### deepseek_reasoner_model

- **类型**: string
- **默认值**: "deepseek-reasoner"
- **说明**: DeepSeek 推理模型名称（用于思考模式）。

**DeepSeek 配置示例**:
```json
{
  "provider": "deepseek",
  "deepseek_api_key": "sk-xxx",
  "deepseek_base_url": "https://api.deepseek.com/v1",
  "deepseek_chat_model": "deepseek-chat",
  "deepseek_reasoner_model": "deepseek-reasoner"
}
```

---

### 图结构检索配置

#### graph_search.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用图结构知识库检索。启用后上传文档时自动提取实体和关系，查询时可通过「模式设置→图结构检索」开关控制。可在前端实时切换。

**示例**:
```json
{
  "graph_search": {
    "enabled": true
  }
}
```

---

### 文档处理配置

#### chunk_size

- **类型**: integer
- **默认值**: 1500
- **说明**: 文档分块大小（字符数）

**调优建议**:
- 小文档/精确问答: 500-1000
- 通用场景: 1000-2000
- 长文档/上下文理解: 2000-3000

---

#### chunk_overlap

- **类型**: integer
- **默认值**: 100
- **说明**: 分块重叠大小（字符数）

**调优建议**: 通常设置为 chunk_size 的 5%-10%

---

### 生成参数配置

#### temperature

- **类型**: float
- **默认值**: 0.7
- **范围**: 0.0 - 2.0
- **说明**: 生成温度，越高越随机

**调优建议**:
- 精确问答: 0.0 - 0.3
- 平衡: 0.5 - 0.8
- 创意生成: 0.8 - 1.5

---

#### top_k

- **类型**: integer
- **默认值**: 5
- **说明**: 检索返回的文档数量

---

#### top_p

- **类型**: float
- **默认值**: 0.9
- **范围**: 0.0 - 1.0
- **说明**: 核采样参数

---

#### max_tokens

- **类型**: integer
- **默认值**: 2048
- **说明**: 最大生成 token 数

---

#### presence_penalty

- **类型**: float
- **默认值**: 0.0
- **范围**: -2.0 - 2.0
- **说明**: 存在惩罚

---

#### frequency_penalty

- **类型**: float
- **默认值**: 0.0
- **范围**: -2.0 - 2.0
- **说明**: 频率惩罚

---

### 系统配置

#### max_history

- **类型**: integer
- **默认值**: 10
- **说明**: 最大历史对话轮数

---

#### upload_max_size

- **类型**: integer
- **默认值**: 104857600 (100MB)
- **说明**: 上传文件最大大小（字节）

---

#### allow_user_registration

- **类型**: boolean
- **默认值**: false
- **说明**: 是否允许用户注册

---

#### allow_pdf_conversion

- **类型**: boolean
- **默认值**: false
- **说明**: 是否启用 PDF 转换功能

---

#### pdf_conversion_method

- **类型**: string
- **默认值**: "marker"
- **可选值**: "marker", "markitdown"
- **说明**: PDF 转 Markdown 的转换方法

**方法对比**:

| 方法 | 说明 | 依赖 | 特点 |
|------|------|------|------|
| marker | 使用 Marker 库 + Surya OCR | marker, torch, transformers | 转换质量高，支持公式和复杂布局，但速度较慢，需要 GPU |
| markitdown | 使用 MarkItDown 库 | markitdown | 轻量级，转换速度快，适合简单 PDF |

**示例**:
```json
{
  "pdf_conversion_method": "markitdown"
}
```

**注意事项**:
- 使用 markitdown 方法需要安装依赖：`pip install 'markitdown[pdf]'`
- marker 方法需要 GPU 支持才能获得较好的性能
- 对于包含复杂公式和布局的 PDF，建议使用 marker 方法
- 对于简单的文本 PDF，markitdown 方法速度更快

---

#### enable_thinking

- **类型**: boolean
- **默认值**: false
- **说明**: 是否启用思考步骤显示

---

### 混合检索配置

```json
{
  "hybrid_search": {
    "enabled": true,
    "initial_retrieve_count": 20,
    "final_select_count": 3,
    "bm25_weight": 0.5,
    "embedding_weight": 0.5,
    "rerank_model": "BAAI/bge-reranker-v2-m3",
    "enable_query_rewrite": true
  }
}
```

#### hybrid_search.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用混合检索

---

#### hybrid_search.initial_retrieve_count

- **类型**: integer
- **默认值**: 20
- **说明**: 初始检索数量

---

#### hybrid_search.final_select_count

- **类型**: integer
- **默认值**: 3
- **说明**: 最终选择数量

---

#### hybrid_search.bm25_weight

- **类型**: float
- **默认值**: 0.5
- **说明**: BM25 检索权重

---

#### hybrid_search.embedding_weight

- **类型**: float
- **默认值**: 0.5
- **说明**: 向量检索权重

---

#### hybrid_search.rerank_model

- **类型**: string
- **默认值**: "BAAI/bge-reranker-v2-m3"
- **说明**: 重排序模型

---

#### hybrid_search.enable_query_rewrite

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用查询重写

---

### 摘要检索配置

```json
{
  "summary_search": {
    "enabled": true,
    "relevance_threshold": 0.6,
    "summary_top_k": 5,
    "content_top_k": 3,
    "auto_generate_summary": true
  }
}
```

#### summary_search.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用摘要检索

---

#### summary_search.relevance_threshold

- **类型**: float
- **默认值**: 0.6
- **说明**: 相关性阈值

---

#### summary_search.summary_top_k

- **类型**: integer
- **默认值**: 5
- **说明**: 摘要检索数量

---

#### summary_search.content_top_k

- **类型**: integer
- **默认值**: 3
- **说明**: 内容检索数量

---

#### summary_search.auto_generate_summary

- **类型**: boolean
- **默认值**: true
- **说明**: 是否自动生成摘要

---

### 上下文管理配置

```json
{
  "context_management": {
    "enabled": true,
    "max_history_rounds": 5,
    "exclude_error_messages": true,
    "exclude_questionable_messages": false
  }
}
```

#### context_management.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用上下文管理

---

#### context_management.max_history_rounds

- **类型**: integer
- **默认值**: 5
- **说明**: 最大历史轮数

---

#### context_management.exclude_error_messages

- **类型**: boolean
- **默认值**: true
- **说明**: 是否排除错误消息

---

## 超时配置 (timeouts)

超时配置用于控制各类操作的最大执行时间：

```json
{
  "timeouts": {
    "enabled": true,
    "requests_post": 60,
    "requests_stream": 60,
    "document_summary": 300,
    "skill_executor_python": 60,
    "skill_executor_shell": 60,
    "react_agent_subprocess": 60,
    "docx2markdown_subprocess": 300
  }
}
```

#### timeouts.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用超时控制

---

#### timeouts.requests_post

- **类型**: integer
- **默认值**: 60
- **说明**: POST 请求超时时间（秒）

---

#### timeouts.requests_stream

- **类型**: integer
- **默认值**: 60
- **说明**: 流式请求超时时间（秒）

---

#### timeouts.document_summary

- **类型**: integer
- **默认值**: 300
- **说明**: 文档摘要生成超时时间（秒）

---

#### timeouts.skill_executor_python

- **类型**: integer
- **默认值**: 60
- **说明**: Python 技能执行器超时时间（秒）

---

#### timeouts.skill_executor_shell

- **类型**: integer
- **默认值**: 60
- **说明**: Shell 技能执行器超时时间（秒）

---

#### timeouts.react_agent_subprocess

- **类型**: integer
- **默认值**: 60
- **说明**: ReAct Agent 子进程超时时间（秒）

---

#### timeouts.docx2markdown_subprocess

- **类型**: integer
- **默认值**: 300
- **说明**: Docx 转 Markdown 子进程超时时间（秒）

---

## 环境变量配置

敏感配置通过环境变量设置，创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/lab_agent.db

# JWT 配置
SECRET_KEY=your-very-strong-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI 配置（仅从环境变量读取）
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 高德天气 API Key（技能使用）
AMAP_API_KEY=79b5363b56d88b0763f983fe4f30be5d
```

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 URL | sqlite:///./data/lab_agent.db |
| SECRET_KEY | JWT 签名密钥 | - |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 过期时间（分钟） | 1440 |
| OPENAI_API_KEY | OpenAI API 密钥 | - |
| OPENAI_BASE_URL | OpenAI API 基础 URL | https://api.openai.com/v1 |
| AMAP_API_KEY | 高德天气 API 密钥 | - |

---

## 技能配置 (skills_config.yaml)

技能系统使用独立的 YAML 配置文件：

```yaml
global:
  enabled: true
  auto_discover: true

arxiv-watcher:
  enabled: true
  version: 1.0.0

amap-weather:
  enabled: true
  version: 1.0.0
```

### 技能配置说明

#### global.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用技能系统

#### global.auto_discover

- **类型**: boolean
- **默认值**: true
- **说明**: 是否自动发现技能目录中的技能

#### {skill_name}.enabled

- **类型**: boolean
- **默认值**: true
- **说明**: 是否启用特定技能

---

## 通过 API 修改配置

可以通过 API 动态修改配置：

### 获取当前配置

```http
GET /api/config
```

### 更新配置

```http
POST /api/config
Content-Type: application/json

{
  "temperature": 0.8,
  "top_k": 10
}
```

---

## 配置推荐

### 开发环境配置

```json
{
  "provider": "openai",
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "chunk_size": 1500,
  "temperature": 0.7,
  "allow_user_registration": true
}
```

### 生产环境配置

```json
{
  "provider": "openai",
  "embedding_mode": "openai",
  "openai_embedding_model": "text-embedding-3-small",
  "openai_chat_model": "gpt-4-turbo-preview",
  "chunk_size": 1500,
  "temperature": 0.5,
  "allow_user_registration": false,
  "hybrid_search": {
    "enabled": true,
    "rerank_model": "BAAI/bge-reranker-v2-m3"
  }
}
```

### 中文优化配置

```json
{
  "local_embedding_model": "BAAI/bge-large-zh-v1.5",
  "chunk_size": 1000,
  "chunk_overlap": 150,
  "hybrid_search": {
    "enabled": true,
    "bm25_weight": 0.6,
    "embedding_weight": 0.4
  }
}
```

### Ollama 本地配置

```json
{
  "provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "qwen3:4b-instruct",
  "embedding_mode": "local",
  "temperature": 0.7
}
```