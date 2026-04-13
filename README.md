# 实验室智能助手 — 完整项目（后端 + 前端）

## 目录

- [项目概述](#项目概述)
- [安装与配置指南](#安装与配置指南)
- [代码结构说明](#代码结构说明)
- [API接口文档](#api接口文档)
- [设计思路](#设计思路)
- [使用示例](#使用示例)
- [参数细节](#参数细节)
- [路径说明](#路径说明)
- [注意事项与常见问题](#注意事项与常见问题)
- [维护与贡献指南](#维护与贡献指南)

---

## 项目概述

### 主要功能

实验室智能助手是一个基于 RAG (Retrieval-Augmented Generation) 技术的智能问答系统，主要功能包括：

1. **知识库管理**：支持 PDF、DOCX、TXT、MD、PPTX、CSV 等多种格式文档的上传、管理和删除
2. **文档向量化**：自动将文档切分并向量化，存储到 Chroma 向量数据库中
3. **智能问答**：基于知识库内容回答用户问题，支持流式输出和引用来源展示
4. **混合检索**：结合向量检索和 BM25 关键词检索，提升检索准确率
5. **文档摘要**：自动生成文档摘要，支持摘要级别的检索
6. **上下文管理**：智能管理对话历史，支持多轮对话
7. **用户认证**：支持用户注册、登录和权限管理
8. **嵌入模型管理**：支持本地嵌入模型和 OpenAI 云端嵌入模型切换
9. **LLM 供应商选择**：支持 OpenAI 云端和 Ollama 本地大语言模型

### 设计理念

- **模块化设计**：后端采用 FastAPI 框架，代码结构清晰，模块职责分明
- **可扩展性**：支持多种嵌入模型和 LLM 供应商，便于后续扩展
- **用户体验优先**：前端采用 Vue 3 + Tailwind CSS，界面简洁美观，操作便捷
- **数据安全**：支持用户认证和权限管理，保护数据安全
- **性能优化**：采用混合检索、重排序等技术，提升检索和回答质量

### 应用场景

- 实验室知识库管理与检索
- 学术论文阅读与问答
- 企业内部文档管理
- 教育培训知识库
- 个人知识管理系统

---

## 安装与配置指南

### 环境依赖清单及版本要求

#### 后端依赖

- Python 3.8+
- FastAPI >= 0.104.0
- Uvicorn[standard] >= 0.24.0
- SQLAlchemy >= 2.0.0
- ChromaDB >= 0.4.0
- Sentence-Transformers >= 2.2.0
- OpenAI >= 1.0.0
- PyPDFPlumber >= 0.10.0
- Python-Docx >= 1.1.0
- Jieba >= 0.42.1
- Torch >= 2.0.0
- Transformers >= 4.35.0

#### 前端依赖

- Node.js 16+
- npm 7+
- Vue 3 >= 3.4.0
- Vite >= 5.0.0
- Tailwind CSS >= 4.2.2
- Axios >= 1.6.0
- Pinia >= 2.1.0
- Vue Router >= 4.2.0

#### 硬件要求

- 4GB+ RAM（推荐 8GB+ 以获得更好性能）
- 10GB+ 磁盘空间（用于存储文档和模型）

### 详细安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd 实验室Agent
```

#### 2. 后端安装与配置

##### 步骤 1：创建虚拟环境（推荐）

```bash
cd backend
python -m venv .venv
```

##### 步骤 2：激活虚拟环境

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

##### 步骤 3：安装依赖

```bash
pip install -r requirements.txt
```

##### 步骤 4：初始化数据库

```bash
python init_db.py
```

##### 步骤 5：配置环境变量（可选）

创建 `.env` 文件在项目根目录：

```env
DATABASE_URL=sqlite:///./data/lab_agent.db
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

##### 步骤 6：启动后端服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将运行在 `http://localhost:8000`

#### 3. 前端安装与配置

##### 步骤 1：安装依赖

```bash
cd frontend
npm install
```

##### 步骤 2：启动开发服务器

```bash
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5175`

##### 步骤 3：构建生产版本（可选）

```bash
npm run build
```

构建产物将输出到 `frontend/dist` 目录

### 配置文件参数说明

#### config.json 配置文件

项目根目录的 `config.json` 是主要配置文件，包含以下参数：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| provider | string | "openai" | LLM 供应商，可选 "openai" 或 "ollama" |
| embedding_mode | string | "local" | 嵌入模式，可选 "local" 或 "openai" |
| local_embedding_model | string | "BAAI/bge-small-zh-v1.5" | 本地嵌入模型名称（Hugging Face 模型 ID） |
| local_model_cache_dir | string | "" | 本地模型缓存目录，留空使用默认目录 |
| openai_api_key | string | "" | OpenAI API 密钥 |
| openai_base_url | string | "https://api.openai.com/v1" | OpenAI API 基础 URL |
| openai_embedding_model | string | "text-embedding-3-small" | OpenAI 嵌入模型 |
| openai_chat_model | string | "gpt-3.5-turbo" | OpenAI 聊天模型 |
| ollama_url | string | "http://localhost:11434" | Ollama 服务地址 |
| ollama_model | string | "" | Ollama 模型名称 |
| chunk_size | integer | 1500 | 文档分块大小（字符数） |
| chunk_overlap | integer | 100 | 分块重叠大小（字符数） |
| temperature | float | 0.7 | 生成温度，0-2 之间，越高越随机 |
| top_k | integer | 5 | 检索返回的文档数量 |
| top_p | float | 0.9 | 核采样参数 |
| max_tokens | integer | 2048 | 最大生成 token 数 |
| presence_penalty | float | 0.0 | 存在惩罚 |
| frequency_penalty | float | 0.0 | 频率惩罚 |
| max_history | integer | 10 | 最大历史对话轮数 |
| upload_max_size | integer | 104857600 | 上传文件最大大小（字节，默认 100MB） |
| enable_thinking | boolean | false | 是否启用思考步骤显示 |
| allow_user_registration | boolean | false | 是否允许用户注册 |
| allow_pdf_conversion | boolean | false | 是否启用 PDF 转换功能 |

#### hybrid_search 子配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | boolean | true | 是否启用混合检索 |
| initial_retrieve_count | integer | 20 | 初始检索数量 |
| final_select_count | integer | 3 | 最终选择数量 |
| bm25_weight | float | 0.5 | BM25 检索权重 |
| embedding_weight | float | 0.5 | 向量检索权重 |
| rerank_model | string | "BAAI/bge-reranker-v2-m3" | 重排序模型 |
| enable_query_rewrite | boolean | true | 是否启用查询重写 |

#### summary_search 子配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | boolean | true | 是否启用摘要检索 |
| relevance_threshold | float | 0.8 | 相关性阈值 |
| summary_top_k | integer | 5 | 摘要检索数量 |
| content_top_k | integer | 3 | 内容检索数量 |
| auto_generate_summary | boolean | true | 是否自动生成摘要 |

#### context_management 子配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | boolean | true | 是否启用上下文管理 |
| max_history_rounds | integer | 5 | 最大历史轮数 |
| exclude_error_messages | boolean | true | 是否排除错误消息 |
| exclude_questionable_messages | boolean | false | 是否排除可疑消息 |

---

## 代码结构说明

### 项目目录结构详解

```
实验室Agent/
├── backend/                 # 后端代码目录
│   ├── app/                 # 应用主目录
│   │   ├── api/             # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py      # 认证相关 API
│   │   │   ├── routes.py    # 主要业务 API
│   │   │   └── sessions.py  # 会话管理 API
│   │   ├── core/            # 核心配置和工具
│   │   │   ├── __init__.py
│   │   │   ├── config.py    # 配置管理
│   │   │   ├── dependencies.py  # 依赖注入
│   │   │   └── rate_limit.py    # 速率限制
│   │   ├── models/          # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # 基础模型
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── session.py   # 会话模型
│   │   │   ├── message.py   # 消息模型
│   │   │   ├── document.py  # 文档模型
│   │   │   ├── audit_log.py # 审计日志模型
│   │   │   ├── permission.py # 权限模型
│   │   │   ├── role_permission.py # 角色权限模型
│   │   │   └── schemas.py   # Pydantic 模式
│   │   ├── services/        # 业务服务层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py      # 认证服务
│   │   │   ├── ingest.py    # 文档处理服务
│   │   │   ├── qa.py        # 问答服务
│   │   │   ├── vector_store.py # 向量存储服务
│   │   │   ├── embedding.py # 嵌入服务
│   │   │   ├── hybrid_search.py # 混合检索服务
│   │   │   ├── bm25_search.py # BM25 检索服务
│   │   │   ├── rerank.py    # 重排序服务
│   │   │   ├── query_rewrite.py # 查询重写服务
│   │   │   ├── document_summary.py # 文档摘要服务
│   │   │   ├── summary_store.py # 摘要存储服务
│   │   │   ├── two_layer_search.py # 双层检索服务
│   │   │   ├── context_manager.py # 上下文管理服务
│   │   │   └── audit.py     # 审计服务
│   │   ├── utils/           # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py # 异常定义
│   │   │   └── file_utils.py # 文件工具
│   │   └── main.py          # FastAPI 应用入口
│   ├── init_db.py           # 数据库初始化脚本
│   ├── manage_users.py      # 用户管理脚本
│   ├── migrate_db.py        # 数据库迁移脚本
│   ├── pdf2markdown.py      # PDF 转 Markdown 脚本
│   ├── docx2markdown.py     # DOCX 转 Markdown 脚本
│   └── requirements.txt     # Python 依赖
├── frontend/                # 前端代码目录
│   ├── src/                 # 源代码
│   │   ├── components/      # 组件
│   │   │   ├── gen-ui/      # 通用 UI 组件
│   │   │   │   ├── CitationHoverCard.vue
│   │   │   │   ├── ComponentRegistry.js
│   │   │   │   ├── DataChart.vue
│   │   │   │   ├── DataTable.vue
│   │   │   │   ├── DocumentPreviewPanel.vue
│   │   │   │   └── ThinkingSteps.vue
│   │   │   ├── Chat.jsx     # 聊天组件
│   │   │   ├── Settings.jsx # 设置组件
│   │   │   ├── Uploads.jsx  # 上传组件
│   │   │   └── ErrorBoundary.jsx # 错误边界
│   │   ├── views/           # 页面视图
│   │   │   ├── ChatView.vue # 聊天页面
│   │   │   ├── LoginView.vue # 登录页面
│   │   │   ├── SettingsView.vue # 设置页面
│   │   │   └── UploadsView.vue # 上传页面
│   │   ├── router/          # 路由
│   │   │   └── index.js
│   │   ├── services/        # API 服务
│   │   │   ├── api.js       # API 客户端
│   │   │   ├── auth.js      # 认证服务
│   │   │   └── sessions.js  # 会话服务
│   │   ├── stores/          # Pinia 状态管理
│   │   │   ├── appStore.js  # 应用状态
│   │   │   └── index.js
│   │   ├── App.jsx          # 应用根组件
│   │   ├── App.vue          # Vue 应用根组件
│   │   ├── main.js          # 入口文件
│   │   ├── main.jsx         # React 入口文件
│   │   └── styles.css       # 全局样式
│   ├── index.html           # HTML 模板
│   ├── vite.config.js       # Vite 配置
│   ├── tailwind.config.cjs  # Tailwind CSS 配置
│   ├── postcss.config.cjs   # PostCSS 配置
│   ├── package.json         # npm 依赖
│   └── dist/                # 构建产物
├── data/                    # 数据目录
│   ├── chroma/              # Chroma 向量数据库
│   ├── uploads/             # 上传的文档
│   ├── summaries/           # 文档摘要
│   ├── lab_agent.db         # SQLite 数据库
│   └── metadata.json        # 文档元数据
├── modelscope_cache/        # ModelScope 模型缓存
├── config.json              # 项目配置文件
├── requirements.txt         # 根目录依赖（与 backend/requirements.txt 相同）
├── LICENSE                  # 许可证
├── README.md                # 本说明文档
├── SQLITE_MIGRATION_GUIDE.md # SQLite 迁移指南
├── GEN_UI_PROGRESS.md      # UI 开发进度
└── 知识库检索优化分析方案.md # 检索优化方案
```

### 核心模块及主要文件功能说明

#### 后端核心模块

1. **app/main.py** - FastAPI 应用入口
   - 创建 FastAPI 应用实例
   - 配置 CORS 中间件
   - 配置速率限制中间件
   - 注册 API 路由

2. **app/api/routes.py** - 主要业务 API
   - 文档上传 API
   - 文档列表和删除 API
   - 问答 API（支持流式输出）
   - 配置管理 API
   - 向量库管理 API
   - 嵌入模型管理 API
   - 文档预览 API
   - 摘要管理 API
   - 上下文管理 API

3. **app/api/auth.py** - 认证 API
   - 用户注册 API
   - 用户登录 API
   - 获取当前用户信息 API
   - 注册配置管理 API

4. **app/services/qa.py** - 问答服务
   - 文档检索
   - LLM 调用
   - 流式输出
   - 输出格式化

5. **app/services/ingest.py** - 文档处理服务
   - 文档文本提取
   - 文档分块
   - 文档向量化
   - 摘要生成

6. **app/services/vector_store.py** - 向量存储服务
   - Chroma 向量库初始化
   - 文档添加
   - 向量检索
   - 文档删除

7. **app/services/hybrid_search.py** - 混合检索服务
   - 结合向量检索和 BM25 检索
   - 结果融合
   - 重排序

8. **app/core/config.py** - 配置管理
   - 配置加载和保存
   - 数据库配置
   - JWT 配置

#### 前端核心模块

1. **src/App.vue** / **src/App.jsx** - 应用根组件
   - 路由配置
   - 布局管理

2. **src/views/ChatView.vue** - 聊天页面
   - 聊天界面
   - 消息展示
   - 引用来源展示

3. **src/views/UploadsView.vue** - 上传页面
   - 文档上传
   - 文档列表
   - 文档管理

4. **src/views/SettingsView.vue** - 设置页面
   - LLM 配置
   - 嵌入模型配置
   - RAG 参数调优

5. **src/services/api.js** - API 客户端
   - Axios 实例配置
   - 请求拦截器（添加认证 token）
   - 响应拦截器（处理认证错误）

6. **src/stores/appStore.js** - 应用状态管理
   - 用户状态
   - 配置状态
   - 会话状态

---

## API接口文档

### 基础信息

- **Base URL**: `http://localhost:8000/api`
- **认证方式**: Bearer Token（可选，部分接口需要）
- **数据格式**: JSON

### 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 接口详细定义

#### 1. 文档管理接口

##### 1.1 上传文档

- **URL**: `/upload`
- **方法**: `POST`
- **Content-Type**: `multipart/form-data`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | files | File[] | 是 | 要上传的文件列表 |
- **响应示例**:
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

##### 1.2 获取文档列表

- **URL**: `/documents`
- **方法**: `GET`
- **响应示例**:
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

##### 1.3 删除文档

- **URL**: `/documents/{filename}` 或 `/documents?file={filename}`
- **方法**: `DELETE`
- **路径参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | filename | string | 是 | 要删除的文件名 |
- **响应示例**:
```json
{
  "status": "deleted",
  "file": "document.md"
}
```

##### 1.4 清空知识库

- **URL**: `/clear`
- **方法**: `POST`
- **响应示例**:
```json
{
  "status": "cleared"
}
```

##### 1.5 获取文档预览

- **URL**: `/document/preview`
- **方法**: `GET`
- **查询参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | filename | string | 是 | 文档文件名 |
  | chunk_index | integer | 否 | 指定 chunk 索引 |
- **响应示例**:
```json
{
  "status": "ok",
  "filename": "document.md",
  "full_text": "文档全文内容...",
  "chunk_content": "指定 chunk 内容...",
  "chunk_index": 0
}
```

#### 2. 问答接口

##### 2.1 问答（流式）

- **URL**: `/qa`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 默认值 | 说明 |
  |--------|------|------|--------|------|
  | question | string | 是 | - | 用户问题 |
  | top_k | integer | 否 | 5 | 检索数量 |
  | provider | string | 否 | null | LLM 供应商 |
  | stream | boolean | 否 | false | 是否流式输出 |
  | temperature | float | 否 | null | 温度参数 |
  | top_p | float | 否 | null | 核采样参数 |
  | max_tokens | integer | 否 | null | 最大 token 数 |
  | presence_penalty | float | 否 | null | 存在惩罚 |
  | frequency_penalty | float | 否 | null | 频率惩罚 |
  | messages | array | 否 | [] | 对话历史 |
- **响应格式**: Server-Sent Events (SSE)
  - 事件类型:
    - `sources`: 引用来源
    - `content`: 回答内容
    - `state`: 状态信息
    - `[DONE]`: 结束信号

#### 3. 配置管理接口

##### 3.1 获取配置

- **URL**: `/config`
- **方法**: `GET`
- **响应示例**: 见 config.json 配置说明

##### 3.2 更新配置

- **URL**: `/config`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求参数**: 任意 config.json 中的配置项
- **响应示例**:
```json
{
  "status": "saved",
  "config": { ... }
}
```

#### 4. 向量库管理接口

##### 4.1 获取向量库状态

- **URL**: `/vector-store/status`
- **方法**: `GET`
- **响应示例**:
```json
{
  "count": 100,
  "metadata": { ... }
}
```

##### 4.2 重置向量库

- **URL**: `/vector-store/reset`
- **方法**: `POST`
- **响应示例**:
```json
{
  "status": "reset",
  "message": "向量库已重置"
}
```

#### 5. 嵌入模型管理接口

##### 5.1 获取推荐模型列表

- **URL**: `/embedding/models/recommended`
- **方法**: `GET`
- **响应示例**:
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

##### 5.2 获取嵌入状态

- **URL**: `/embedding/status`
- **方法**: `GET`
- **响应示例**:
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

##### 5.3 设置嵌入模式

- **URL**: `/embedding/mode`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 默认值 | 说明 |
  |--------|------|------|--------|------|
  | mode | string | 是 | - | "local" 或 "openai" |
  | reset_collection | boolean | 否 | false | 是否重置向量库 |
- **响应示例**:
```json
{
  "status": "ok",
  "message": "已切换到 local 模式",
  "reset_collection": false
}
```

##### 5.4 设置本地嵌入模型

- **URL**: `/embedding/local-model`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | model_name | string | 是 | 模型名称 |
  | cache_dir | string | 否 | 缓存目录 |
- **响应示例**:
```json
{
  "status": "ok",
  "message": "本地模型已设置为: BAAI/bge-small-zh-v1.5",
  "model_name": "BAAI/bge-small-zh-v1.5"
}
```

#### 6. 摘要管理接口

##### 6.1 列出所有摘要

- **URL**: `/summaries`
- **方法**: `GET`
- **响应示例**:
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

##### 6.2 获取指定文档摘要

- **URL**: `/summaries/{filename}`
- **方法**: `GET`
- **响应示例**:
```json
{
  "status": "ok",
  "summary": { ... }
}
```

##### 6.3 重新生成摘要

- **URL**: `/summaries/{filename}/regenerate`
- **方法**: `POST`
- **查询参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | provider | string | 否 | LLM 供应商 |
- **响应示例**:
```json
{
  "status": "ok",
  "message": "摘要重新生成成功",
  "summary": { ... }
}
```

#### 7. 上下文管理接口

##### 7.1 获取上下文历史

- **URL**: `/context/{session_id}`
- **方法**: `GET`
- **路径参数**:
  | 参数名 | 类型 | 必填 | 默认值 | 说明 |
  |--------|------|------|--------|------|
  | session_id | string | 否 | "default" | 会话 ID |
- **响应示例**:
```json
{
  "status": "ok",
  "history": [ ... ],
  "stats": { ... }
}
```

##### 7.2 清除上下文历史

- **URL**: `/context/{session_id}`
- **方法**: `DELETE`
- **路径参数**:
  | 参数名 | 类型 | 必填 | 默认值 | 说明 |
  |--------|------|------|--------|------|
  | session_id | string | 否 | "default" | 会话 ID |
- **响应示例**:
```json
{
  "status": "ok",
  "message": "会话 default 的上下文历史已清除"
}
```

#### 8. 认证接口

##### 8.1 用户注册

- **URL**: `/auth/register`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | username | string | 是 | 用户名 |
  | email | string | 是 | 邮箱 |
  | password | string | 是 | 密码（至少 8 位） |
- **响应示例**:
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

##### 8.2 用户登录

- **URL**: `/auth/login`
- **方法**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`
- **请求参数**:
  | 参数名 | 类型 | 必填 | 说明 |
  |--------|------|------|------|
  | username | string | 是 | 用户名 |
  | password | string | 是 | 密码 |
- **响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 设计思路

### 项目架构设计

项目采用前后端分离的架构设计：

1. **后端架构**
   - 采用 FastAPI 作为 Web 框架，提供高性能的 RESTful API
   - 使用 SQLAlchemy 作为 ORM，支持 SQLite 数据库
   - 采用分层架构：API 层 → 服务层 → 数据层
   - 使用 Chroma 作为向量数据库，存储文档向量
   - 支持多种嵌入模型和 LLM 供应商

2. **前端架构**
   - 采用 Vue 3 作为前端框架，使用 Composition API
   - 使用 Vite 作为构建工具，提供快速的开发体验
   - 使用 Tailwind CSS 进行样式开发
   - 使用 Pinia 进行状态管理
   - 使用 Vue Router 进行路由管理

### 核心算法或关键逻辑的实现思路

#### 1. RAG 检索增强生成

RAG (Retrieval-Augmented Generation) 是本项目的核心技术，实现思路如下：

1. **文档处理阶段**
   - 提取文档文本内容
   - 将文档切分为适当大小的 chunk
   - 为每个 chunk 生成向量嵌入
   - 存储到向量数据库

2. **检索阶段**
   - 将用户问题转换为向量
   - 在向量数据库中检索相似的文档 chunk
   - 可选：使用 BM25 进行关键词检索
   - 可选：对检索结果进行重排序

3. **生成阶段**
   - 将检索到的文档 chunk 作为上下文
   - 构建提示词（包含上下文和用户问题）
   - 调用 LLM 生成回答
   - 流式输出回答内容

#### 2. 混合检索

混合检索结合了向量检索和 BM25 关键词检索的优势：

1. **向量检索**：擅长语义匹配，能理解同义词和上下文
2. **BM25 检索**：擅长精确关键词匹配，对特定术语敏感
3. **结果融合**：将两种检索结果按权重融合
4. **重排序**：使用重排序模型对融合结果进行精细排序

#### 3. 双层检索

双层检索结合了摘要检索和内容检索：

1. **第一层**：在文档摘要中检索，快速定位相关文档
2. **第二层**：在相关文档的内容中进行精细检索
3. **优势**：提高检索效率，减少无关内容的干扰

#### 4. 查询重写

查询重写用于优化用户问题，提高检索准确率：

1. 分析用户问题的意图
2. 扩展问题的关键词
3. 改写问题使其更清晰
4. 使用重写后的问题进行检索

### 技术选型理由及优势分析

#### 后端技术选型

1. **FastAPI**
   - 理由：高性能、自动生成 API 文档、类型提示支持
   - 优势：基于 Starlette 和 Pydantic，性能接近 Node.js 和 Go

2. **Chroma**
   - 理由：轻量级、易于部署、Python 原生支持
   - 优势：无需额外部署数据库，适合中小规模应用

3. **Sentence-Transformers**
   - 理由：提供高质量的预训练嵌入模型
   - 优势：支持多种语言，易于使用

4. **SQLAlchemy**
   - 理由：成熟的 ORM 框架，支持多种数据库
   - 优势：灵活、可扩展，便于未来切换数据库

#### 前端技术选型

1. **Vue 3**
   - 理由：渐进式框架、学习曲线平缓、Composition API
   - 优势：性能优秀，生态系统完善

2. **Vite**
   - 理由：极速的冷启动和热更新
   - 优势：开发体验极佳，构建速度快

3. **Tailwind CSS**
   - 理由：实用优先的 CSS 框架，快速开发
   - 优势：减少 CSS 文件体积，易于维护

4. **Pinia**
   - 理由：Vue 3 官方推荐的状态管理库
   - 优势：简洁、类型安全、易于调试

---

## 使用示例

### 完整的使用流程示例

#### 1. 初始化项目

```bash
# 克隆项目
git clone <repository-url>
cd 实验室Agent

# 安装后端依赖
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
python init_db.py

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 新开终端，安装前端依赖
cd frontend
npm install

# 启动前端
npm run dev
```

#### 2. 配置系统

打开浏览器访问 `http://localhost:5175`，进入设置页面：

1. 选择 LLM 供应商（OpenAI 或 Ollama）
2. 配置 API 密钥和基础 URL
3. 选择嵌入模式（本地或 OpenAI）
4. 调整 RAG 参数（分块大小、重叠度、温度等）
5. 点击「应用更改」保存配置

#### 3. 上传文档

1. 点击左侧导航栏的「知识库」
2. 点击「选择文件」按钮，选择要上传的文档
3. 点击「同步知识库」开始上传和处理
4. 等待处理完成，文档会显示在列表中

#### 4. 开始对话

1. 点击左侧导航栏的「对话」
2. 在输入框中输入问题，例如：「请介绍一下这篇论文的主要贡献」
3. 点击发送按钮，系统会基于知识库内容生成回答
4. 查看回答和引用的文档来源
5. 可以继续提问，进行多轮对话

### 关键功能的代码示例或操作步骤

#### 示例 1：使用 API 上传文档

```javascript
import api from './services/api'

const uploadDocuments = async (files) => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  
  try {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    console.log('上传成功:', response.data)
    return response.data
  } catch (error) {
    console.error('上传失败:', error)
    throw error
  }
}
```

#### 示例 2：使用 API 进行问答（流式）

```javascript
import api from './services/api'

const askQuestion = async (question, onData, onComplete) => {
  try {
    const response = await api.post('/qa', {
      question: question,
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
          if (data === '[DONE]') {
            continue
          }
          try {
            const parsed = JSON.parse(data)
            onData && onData(parsed)
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (error) {
    console.error('问答失败:', error)
    throw error
  }
}
```

#### 示例 3：Python 后端调用 LLM

```python
from app.core.config import load_config
from openai import OpenAI

def call_llm(prompt: str, provider: str = "openai"):
    cfg = load_config()
    
    if provider == "openai":
        client = OpenAI(
            api_key=cfg.get("openai_api_key"),
            base_url=cfg.get("openai_base_url")
        )
        
        response = client.chat.completions.create(
            model=cfg.get("openai_chat_model"),
            messages=[{"role": "user", "content": prompt}],
            temperature=cfg.get("temperature"),
            max_tokens=cfg.get("max_tokens")
        )
        
        return response.choices[0].message.content
    
    elif provider == "ollama":
        import requests
        
        response = requests.post(
            f"{cfg.get('ollama_url')}/api/generate",
            json={
                "model": cfg.get("ollama_model"),
                "prompt": prompt,
                "stream": False
            }
        )
        
        return response.json().get("response")
```

---

## 参数细节

### 函数、方法参数说明

#### backend/app/services/qa.py 中的核心函数

##### `answer_question(question, provider, top_k, session_id)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| question | string | - | 用户问题 |
| provider | string | "openai" | LLM 供应商 |
| top_k | integer | 5 | 检索文档数量 |
| session_id | string | "default" | 会话 ID |
| **返回值** | Tuple[str, List[dict]] | - | (回答内容, 引用来源列表) |

##### `stream_answer(question, provider, include_state, **kwargs)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| question | string | - | 用户问题 |
| provider | string | "openai" | LLM 供应商 |
| include_state | boolean | False | 是否包含状态事件 |
| **kwargs | dict | - | 其他生成参数 |
| **返回值** | Generator | - | 流式生成器 |

#### backend/app/services/ingest.py 中的核心函数

##### `ingest_file(file_path, provider)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| file_path | string | - | 文件路径 |
| provider | string | "openai" | LLM 供应商 |
| **返回值** | dict | - | 处理结果 |

##### `extract_text(file_path)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| file_path | string | - | 文件路径 |
| **返回值** | string | - | 提取的文本内容 |

#### backend/app/services/vector_store.py 中的核心函数

##### `search(query, top_k, provider)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| query | string | - | 查询文本 |
| top_k | integer | 5 | 返回结果数量 |
| provider | string | "openai" | LLM 供应商 |
| **返回值** | List[dict] | - | 检索结果列表 |

##### `add_documents(documents, metadatas, provider)`

| 参数名 | 类型 | 默认值 | 用途 |
|--------|------|--------|------|
| documents | List[string] | - | 文档内容列表 |
| metadatas | List[dict] | - | 元数据列表 |
| provider | string | "openai" | LLM 供应商 |
| **返回值** | List[string] | - | 文档 ID 列表 |

---

## 路径说明

### 关键文件路径说明

| 路径 | 说明 |
|------|------|
| `backend/app/main.py` | FastAPI 应用入口 |
| `backend/app/api/routes.py` | 主要业务 API 路由 |
| `backend/app/api/auth.py` | 认证 API 路由 |
| `backend/app/core/config.py` | 配置管理 |
| `backend/app/services/qa.py` | 问答服务 |
| `backend/app/services/ingest.py` | 文档处理服务 |
| `backend/app/services/vector_store.py` | 向量存储服务 |
| `backend/app/services/hybrid_search.py` | 混合检索服务 |
| `backend/init_db.py` | 数据库初始化脚本 |
| `frontend/src/App.vue` | 前端应用根组件 |
| `frontend/src/views/ChatView.vue` | 聊天页面 |
| `frontend/src/views/UploadsView.vue` | 上传页面 |
| `frontend/src/views/SettingsView.vue` | 设置页面 |
| `frontend/src/services/api.js` | API 客户端 |
| `config.json` | 项目配置文件 |
| `data/lab_agent.db` | SQLite 数据库文件 |
| `data/chroma/` | Chroma 向量数据库目录 |
| `data/uploads/` | 上传文档存储目录 |
| `data/summaries/` | 文档摘要存储目录 |

### 资源文件存放位置及引用方式

#### 上传文档

- **存放位置**: `data/uploads/`
- **引用方式**: 通过文件名引用，如 `data/uploads/document.md`
- **元数据**: 存储在 `data/metadata.json`

#### 向量数据库

- **存放位置**: `data/chroma/`
- **引用方式**: 通过 Chroma API 访问
- **说明**: 包含文档向量和元数据

#### 文档摘要

- **存放位置**: `data/summaries/`
- **引用方式**: 通过文件名引用，如 `data/summaries/{hash}.json`
- **索引**: `data/summaries/summary_index.json`

#### 模型缓存

- **存放位置**: `modelscope_cache/` 或 Hugging Face 默认缓存目录
- **引用方式**: 通过模型名称自动加载
- **说明**: 本地嵌入模型和重排序模型的缓存

---

## 注意事项与常见问题

### 使用过程中的注意事项

1. **首次使用本地嵌入模型**
   - 首次使用本地嵌入模型时需要下载模型，确保网络连接正常
   - 模型文件较大，可能需要较长时间下载
   - 下载的模型会缓存到本地，后续使用无需重新下载

2. **切换嵌入模型**
   - 切换嵌入模型或嵌入模式后，向量维度可能改变
   - 必须重置向量库并重新上传文档
   - 在 config.json 中设置 `embedding_mode` 或通过 API 切换

3. **文档上传大小限制**
   - 默认上传文件大小限制为 100MB
   - 可通过 config.json 中的 `upload_max_size` 参数调整
   - 大文件上传可能需要较长时间处理

4. **内存使用**
   - 本地嵌入模型会占用较多内存
   - 建议使用 8GB+ RAM 以获得更好性能
   - 如内存不足，可选择较小的嵌入模型

5. **用户认证**
   - 默认情况下用户注册功能关闭
   - 可通过 config.json 中的 `allow_user_registration` 启用
   - 生产环境请修改 `SECRET_KEY`

### 常见问题及解决方案

#### 问题 1：后端启动失败

**症状**: 运行 `uvicorn app.main:app` 时报错

**解决方案**:
1. 检查 Python 版本是否满足要求（3.8+）
2. 检查依赖是否正确安装：`pip list`
3. 检查端口 8000 是否被占用
4. 查看终端输出的错误信息
5. 尝试删除 `data/lab_agent.db` 并重新运行 `python init_db.py`

#### 问题 2：前端无法连接后端

**症状**: 前端显示网络错误或无法加载数据

**解决方案**:
1. 确认后端服务正在运行
2. 检查 `frontend/vite.config.js` 中的代理配置
3. 确认后端地址和端口正确
4. 检查浏览器控制台的错误信息

#### 问题 3：文档上传失败

**症状**: 点击上传后没有反应或显示错误

**解决方案**:
1. 检查文档格式是否支持（PDF、DOCX、TXT、MD 等）
2. 检查文档大小是否超过限制
3. 确认后端服务正常运行
4. 查看后端终端的错误日志
5. 尝试上传较小的测试文件

#### 问题 4：聊天功能无响应

**症状**: 发送问题后没有回答或加载时间过长

**解决方案**:
1. 检查后端服务是否正常运行
2. 检查 LLM 配置是否正确（API 密钥、URL 等）
3. 确认知识库中有文档
4. 检查网络连接（如使用云端 LLM）
5. 查看后端终端的错误日志

#### 问题 5：本地嵌入模型加载失败

**症状**: 后端报错显示无法加载嵌入模型

**解决方案**:
1. 确认已安装 sentence-transformers：`pip install sentence-transformers>=2.2.0`
2. 检查网络连接（首次使用需要下载模型）
3. 检查内存是否足够
4. 尝试使用更小的模型，如 `BAAI/bge-small-zh-v1.5`
5. 查看后端终端的错误日志

#### 问题 6：检索结果不准确

**症状**: 回答与问题不相关或引用错误的文档

**解决方案**:
1. 调整 `top_k` 参数，增加检索数量
2. 启用混合检索（`hybrid_search.enabled: true`）
3. 调整 BM25 和向量检索的权重
4. 尝试启用查询重写（`enable_query_rewrite: true`）
5. 检查文档分块大小是否合适

---

## 维护与贡献指南

### 代码规范说明

#### 后端代码规范（Python）

1. **遵循 PEP 8 风格指南**
   - 使用 4 空格缩进
   - 行长度不超过 120 字符
   - 使用有意义的变量和函数名

2. **类型提示**
   - 所有函数都应添加类型提示
   - 使用 `typing` 模块中的类型

3. **文档字符串**
   - 所有公共函数和类都应添加文档字符串
   - 使用 Google 风格或 NumPy 风格的文档字符串

4. **错误处理**
   - 合理使用异常处理
   - 定义自定义异常类

#### 前端代码规范（Vue/JavaScript）

1. **Vue 风格指南**
   - 遵循 Vue 3 官方风格指南
   - 使用 Composition API
   - 组件名使用 PascalCase

2. **代码格式化**
   - 使用 Prettier 格式化代码
   - 使用 ESLint 检查代码质量

3. **命名规范**
   - 组件名：PascalCase（如 `ChatView.vue`）
   - 变量和函数：camelCase（如 `handleClick`）
   - 常量：UPPER_SNAKE_CASE（如 `MAX_SIZE`）

4. **组件设计**
   - 保持组件单一职责
   - 合理使用 props 和 emits
   - 使用 Pinia 管理共享状态

### 贡献代码的流程

1. **Fork 项目**
   - 在 GitHub 上 Fork 本项目到自己的账号

2. **克隆项目**
   ```bash
   git clone https://github.com/Philos01/Ex-Agent.git
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **编写代码**
   - 遵循代码规范
   - 添加必要的注释和文档
   - 确保代码能正常运行

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   # 或
   git commit -m "fix: 修复某个 bug"
   ```

6. **推送到远程**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 详细描述你的更改内容
   - 等待代码审查

8. **代码审查**
   - 根据审查意见修改代码
   - 更新 Pull Request

9. **合并**
   - 代码审查通过后，会被合并到主分支

### 提交信息规范

使用语义化的提交信息：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加文档重排序功能
fix: 修复上传大文件时的内存溢出问题
docs: 更新 README 中的配置说明
```

---

## 技术栈总结

### 后端技术栈

- **Web 框架**: FastAPI
- **ASGI 服务器**: Uvicorn
- **数据库 ORM**: SQLAlchemy
- **向量数据库**: Chroma
- **嵌入模型**: Sentence-Transformers
- **LLM 集成**: OpenAI SDK, Ollama
- **文件处理**: PyPDFPlumber, Python-Docx, Mammoth
- **文本检索**: Jieba, BM25
- **深度学习**: PyTorch, Transformers
- **认证**: Python-JOSE, Bcrypt

### 前端技术栈

- **前端框架**: Vue 3
- **构建工具**: Vite
- **CSS 框架**: Tailwind CSS
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **Markdown 解析**: Marked

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request！

---

**感谢使用实验室智能助手！**
