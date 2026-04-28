# 后端开发文档

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

后端采用分层架构设计，各层职责清晰，便于维护和扩展：

```
┌─────────────────────────────────────────────────────────┐
│                      API 层 (API Layer)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ routes.py    │  │ auth.py      │  │ sessions.py  │  │
│  │ skills.py    │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ v1/          │  │              │  │              │  │
│  │  api_router  │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    服务层 (Service Layer)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ qa.py    │  │ ingest.py│  │ auth.py  │  │ audit.py ││
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤│
│  │ vector_  │  │ hybrid_  │  │ bm25_    │  │ rerank.py││
│  │ store.py │  │ search.py│  │ search.py│  │          ││
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤│
│  │ doc_     │  │ summary_ │  │ query_   │  │ context_ ││
│  │ summary. │  │ store.py │  │ rewrite.py│  │ manager. ││
│  │ py       │  │          │  │          │  │ py       ││
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤│
│  │ two_     │  │ embed-   │  │          │  │          ││
│  │ layer_    │  │ ding.py  │  │          │  │          ││
│  │ search.py │  │          │  │          │  │          ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│     模型层     │  │   技能系统     │  │   Agent 系统   │
│  (Data Layer) │  │  (Skills)     │  │  (Agents)     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ user.py       │  │ base.py       │  │ react_agent.py│
│ session.py    │  │ discovery.py  │  │ memory.py     │
│ message.py    │  │ executor.py   │  │ prompt_engine.│
│ document.py   │  │ manager.py    │  │ py            │
│ audit_log.py  │  │ selector.py   │  │ output_parser.│
│ permission.py │  │ metadata_     │  │ py            │
│ role_         │  │ parser.py     │  │               │
│ permission.py │  │               │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   基础设施层 (Infrastructure)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │config.py │  │dependen- │  │rate_     │  │logging_   ││
│  │          │  │cies.py   │  │limit.py  │  │config.py  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
```

### 设计模式

1. **分层架构模式**：API 层 → 服务层 → 数据层
2. **依赖注入模式**：通过 `dependencies.py` 实现
3. **工厂模式**：用于创建不同的 LLM 客户端和嵌入模型
4. **策略模式**：用于不同的检索算法和重排序策略
5. **中间件模式**：用于速率限制、CORS 等横切关注点

---

## 技术栈选型

### 核心框架

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|----------|
| FastAPI | >= 0.104.0 | Web 框架 | 高性能、自动生成 API 文档、类型提示支持 |
| Uvicorn | >= 0.24.0 | ASGI 服务器 | 高性能异步服务器，与 FastAPI 完美配合 |
| SQLAlchemy | >= 2.0.0 | ORM | 成熟的 ORM 框架，支持多种数据库 |
| ChromaDB | >= 0.4.0 | 向量数据库 | 轻量级、易于部署、Python 原生支持 |

### 数据处理

| 技术 | 版本 | 用途 |
|------|------|------|
| Sentence-Transformers | >= 2.2.0 | 文本嵌入 |
| PyTorch | >= 2.0.0 | 深度学习框架 |
| Transformers | >= 4.35.0 | 预训练模型 |
| Jieba | >= 0.42.1 | 中文分词 |

### 文件处理

| 技术 | 版本 | 用途 |
|------|------|------|
| pdfplumber | >= 0.10.0 | PDF 文本提取 |
| python-docx | >= 1.1.0 | DOCX 文档处理 |
| mammoth | >= 1.6.0 | DOCX 转 HTML/Markdown |
| openpyxl | >= 3.1.0 | Excel 文件处理 |
| markitdown | >= 0.0.1 | PDF/Excel 转 Markdown（支持配置切换）|
| marker | >= 1.0.0 | PDF 转 Markdown（高准确率，需要 GPU）|

### 认证与安全

| 技术 | 版本 | 用途 |
|------|------|------|
| bcrypt | >= 4.0.0 | 密码哈希 |
| python-jose | >= 3.3.0 | JWT 认证 |
| python-multipart | >= 0.0.6 | 文件上传 |

### LLM 集成

| 技术 | 版本 | 用途 |
|------|------|------|
| openai | >= 1.0.0 | OpenAI API 客户端 |
| requests | >= 2.31.0 | HTTP 请求（用于 Ollama） |

---

## 核心功能实现

### 1. RAG 检索增强生成

RAG 是本项目的核心技术，实现流程如下：

#### 文档处理阶段

```python
# backend/app/services/ingest.py
def ingest_file(file_path: str, provider: str = "openai"):
    # 1. 提取文本（支持多种格式）
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        # Excel 文件使用 MarkItDown 转换为 Markdown
        text = extract_excel_as_markdown(file_path)
    else:
        text = extract_text(file_path)

    # 2. 文档分块
    chunks = split_text(text, chunk_size, chunk_overlap)

    # 3. 生成向量嵌入
    embeddings = get_embeddings(chunks)

    # 4. 存储到向量数据库
    vector_store.add_documents(chunks, metadatas)

    # 5. 生成文档摘要
    if auto_generate_summary:
        summary = generate_document_summary(text)
        save_summary(summary)
```

**支持的文档格式**:
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls) - 使用 MarkItDown 转换为 Markdown
- 纯文本 (.txt)
- Markdown (.md)
- PowerPoint (.pptx)

#### 检索阶段

```python
# backend/app/services/qa.py
def retrieve_context(question: str, top_k: int = 5):
    # 1. 查询重写（可选）
    if enable_query_rewrite:
        question = rewrite_query(question)

    # 2. 混合检索
    if hybrid_search_enabled:
        results = hybrid_search.search(question, top_k)
    else:
        results = vector_store.search(question, top_k)

    # 3. 重排序（可选）
    if rerank_enabled:
        results = rerank.rerank(question, results)

    return results
```

#### 生成阶段

```python
# backend/app/services/qa.py
def generate_answer(question: str, context: List[dict]):
    # 1. 构建提示词
    prompt = build_prompt(question, context)

    # 2. 调用 LLM
    response = llm_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    # 3. 流式输出
    for chunk in response:
        yield chunk.choices[0].delta.content
```

### 2. 混合检索

混合检索结合了向量检索和 BM25 关键词检索：

```python
# backend/app/services/hybrid_search.py
class HybridSearch:
    def search(self, query: str, top_k: int = 5):
        # 1. 向量检索
        vector_results = vector_store.search(query, initial_retrieve_count)

        # 2. BM25 检索
        bm25_results = bm25_search.search(query, initial_retrieve_count)

        # 3. 结果融合
        fused_results = self.fuse_results(vector_results, bm25_results)

        # 4. 重排序
        reranked_results = rerank.rerank(query, fused_results)

        return reranked_results[:top_k]
```

### 3. 双层检索

结合摘要检索和内容检索：

```python
# backend/app/services/two_layer_search.py
class TwoLayerSearch:
    def search(self, query: str):
        # 第一层：摘要检索
        summary_results = summary_store.search(query, summary_top_k)

        # 第二层：在相关文档内容中检索
        content_results = []
        for summary in summary_results:
            doc_results = vector_store.search_in_document(
                query, summary.filename, content_top_k
            )
            content_results.extend(doc_results)

        return content_results
```

### 4. 用户认证

使用 JWT 进行用户认证：

```python
# backend/app/services/auth.py
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### 5. 速率限制

系统内置速率限制功能：

```python
# backend/app/core/rate_limit.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

login_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per hour"]
)

api_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)
```

### 6. 技能系统

技能系统允许扩展系统能力：

```python
# backend/app/skills/base.py
class Skill(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, params: dict) -> Any:
        pass

    def should_use(self, query: str) -> bool:
        return False
```

技能选择器根据用户查询自动选择合适的技能执行。

### 7. Agent 系统 (ReAct)

支持 ReAct (Reasoning + Acting) 模式的 Agent：

```python
# backend/app/agents/react_agent.py
class ReActAgent:
    def __init__(self, llm_client, tools: List[Skill]):
        self.llm_client = llm_client
        self.tools = tools
        self.memory = WorkingMemory()

    async def run(self, query: str) -> str:
        thought = await self.reason(query)
        action = await self.act(thought)
        observation = await self.execute(action)
        # 循环直到完成
```

---

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── api/                       # API 路由
│   │   ├── __init__.py
│   │   ├── v1/                   # v1 版本 API
│   │   │   ├── __init__.py
│   │   │   ├── api_router.py    # v1 路由汇总
│   │   │   ├── auth.py          # 认证 API
│   │   │   ├── routes.py        # 主要业务 API
│   │   │   ├── sessions.py       # 会话管理 API
│   │   │   └── skills.py        # 技能 API
│   │   ├── auth.py              # 认证 API (原始版本)
│   │   ├── routes.py            # 主要业务 API (原始版本)
│   │   ├── sessions.py          # 会话管理 API (原始版本)
│   │   └── skills.py            # 技能 API (原始版本)
│   ├── core/                     # 核心配置和工具
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理
│   │   ├── dependencies.py      # 依赖注入
│   │   ├── logging_config.py    # 日志配置
│   │   └── rate_limit.py        # 速率限制
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py              # 基础模型
│   │   ├── user.py              # 用户模型
│   │   ├── session.py           # 会话模型
│   │   ├── message.py           # 消息模型
│   │   ├── document.py          # 文档模型
│   │   ├── audit_log.py         # 审计日志模型
│   │   ├── permission.py         # 权限模型
│   │   ├── role_permission.py   # 角色权限模型
│   │   └── schemas.py           # Pydantic 模式
│   ├── services/                 # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证服务
│   │   ├── ingest.py            # 文档处理服务
│   │   ├── qa.py                # 问答服务
│   │   ├── vector_store.py      # 向量存储服务
│   │   ├── embedding.py         # 嵌入服务
│   │   ├── hybrid_search.py     # 混合检索服务
│   │   ├── bm25_search.py       # BM25 检索服务
│   │   ├── rerank.py            # 重排序服务
│   │   ├── query_rewrite.py     # 查询重写服务
│   │   ├── document_summary.py  # 文档摘要服务
│   │   ├── summary_store.py     # 摘要存储服务
│   │   ├── two_layer_search.py  # 双层检索服务
│   │   ├── context_manager.py   # 上下文管理服务
│   │   └── audit.py             # 审计服务
│   ├── skills/                   # 技能系统
│   │   ├── __init__.py
│   │   ├── base.py              # 技能基类
│   │   ├── discovery.py         # 技能发现
│   │   ├── metadata_parser.py   # 元数据解析
│   │   ├── skill_executor.py    # 技能执行器
│   │   ├── skill_manager.py     # 技能管理器
│   │   └── skill_selector.py    # 技能选择器
│   ├── agents/                   # Agent 系统
│   │   ├── __init__.py
│   │   ├── exceptions.py        # 异常定义
│   │   ├── memory.py            # 记忆管理
│   │   ├── output_parser.py     # 输出解析器
│   │   ├── prompt_engine.py     # 提示词引擎
│   │   └── react_agent.py       # ReAct Agent
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── exceptions.py         # 异常定义
│       └── file_utils.py        # 文件工具
├── scripts/                      # 脚本工具
│   ├── check_paths.py
│   ├── check_root.py
│   ├── check_vector_store.py
│   ├── docx2markdown.py
│   ├── init_db.py               # 数据库初始化
│   ├── manage_users.py          # 用户管理
│   ├── migrate_db.py            # 数据库迁移
│   ├── pdf2markdown.py
│   └── skill_deployer.py       # 技能部署
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_rag.py
│   ├── test_rate_limit.py
│   ├── test_security.py
│   └── test_skills.py
├── pytest.ini
└── requirements.txt             # Python 依赖
```

---

## 配置指南

### 配置文件结构

主要配置文件为 `config.json`，位于项目根目录。

#### 完整配置示例

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
  "skills": {
    "enabled": true,
    "arxiv_search": {
      "enabled": true,
      "max_results": 5
    }
  }
}
```

#### 配置参数说明

##### 基础配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| provider | string | "openai" | LLM 供应商，可选 "openai" 或 "ollama" |
| embedding_mode | string | "local" | 嵌入模式，可选 "local" 或 "openai" |
| local_embedding_model | string | "BAAI/bge-small-zh-v1.5" | 本地嵌入模型名称 |
| openai_base_url | string | "https://api.openai.com/v1" | OpenAI API 基础 URL |
| openai_embedding_model | string | "text-embedding-3-small" | OpenAI 嵌入模型 |
| openai_chat_model | string | "gpt-3.5-turbo" | OpenAI 聊天模型 |
| ollama_url | string | "http://localhost:11434" | Ollama 服务地址 |
| ollama_model | string | "" | Ollama 模型名称 |

##### 文档处理配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| chunk_size | integer | 1500 | 文档分块大小（字符数） |
| chunk_overlap | integer | 100 | 分块重叠大小（字符数） |

##### 生成参数配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| temperature | float | 0.7 | 生成温度，0-2 之间 |
| top_k | integer | 5 | 检索返回的文档数量 |
| top_p | float | 0.9 | 核采样参数 |
| max_tokens | integer | 2048 | 最大生成 token 数 |
| presence_penalty | float | 0.0 | 存在惩罚 |
| frequency_penalty | float | 0.0 | 频率惩罚 |

##### 系统配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| max_history | integer | 10 | 最大历史对话轮数 |
| upload_max_size | integer | 104857600 | 上传文件最大大小（字节） |
| allow_user_registration | boolean | false | 是否允许用户注册 |
| allow_pdf_conversion | boolean | false | 是否启用 PDF 转换功能 |
| enable_thinking | boolean | false | 是否启用思考步骤显示 |

##### 混合检索配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| hybrid_search.enabled | boolean | true | 是否启用混合检索 |
| hybrid_search.initial_retrieve_count | integer | 20 | 初始检索数量 |
| hybrid_search.final_select_count | integer | 3 | 最终选择数量 |
| hybrid_search.bm25_weight | float | 0.5 | BM25 检索权重 |
| hybrid_search.embedding_weight | float | 0.5 | 向量检索权重 |
| hybrid_search.rerank_model | string | "BAAI/bge-reranker-v2-m3" | 重排序模型 |
| hybrid_search.enable_query_rewrite | boolean | true | 是否启用查询重写 |

##### 摘要检索配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| summary_search.enabled | boolean | true | 是否启用摘要检索 |
| summary_search.relevance_threshold | float | 0.6 | 相关性阈值 |
| summary_search.summary_top_k | integer | 5 | 摘要检索数量 |
| summary_search.content_top_k | integer | 3 | 内容检索数量 |
| summary_search.auto_generate_summary | boolean | true | 是否自动生成摘要 |

##### 上下文管理配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| context_management.enabled | boolean | true | 是否启用上下文管理 |
| context_management.max_history_rounds | integer | 5 | 最大历史轮数 |
| context_management.exclude_error_messages | boolean | true | 是否排除错误消息 |

##### 技能系统配置

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| skills.enabled | boolean | true | 是否启用技能系统 |
| skills.arxiv_search.enabled | boolean | true | 是否启用 ArXiv 搜索 |
| skills.arxiv_search.max_results | integer | 5 | ArXiv 最大结果数 |

### 环境变量配置

敏感信息通过环境变量配置，创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/lab_agent.db

# JWT 配置
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI 配置（仅从环境变量读取，不保存到配置文件）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 高德天气 API Key（技能使用）
AMAP_API_KEY=79b5363b56d88b0763f983fe4f30be5d
```

---

## 开发环境搭建

### 系统要求

- Python 3.8+ (推荐 3.10+)
- pip 20.0+
- 4GB+ RAM（推荐 8GB+）
- 10GB+ 磁盘空间

### 步骤 1：克隆项目

```bash
git clone <repository-url>
cd 实验室Agent/backend
```

### 步骤 2：创建虚拟环境

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 步骤 3：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4：初始化数据库

```bash
cd scripts
python init_db.py create
```

### 步骤 5：配置环境变量

在项目根目录创建 `.env` 文件（参考上文）。

### 步骤 6：启动开发服务器

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 验证安装

访问以下地址验证后端服务是否正常：

- 根路径: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 备用文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/health

### 开发工具推荐

- **IDE**: PyCharm 或 VS Code
- **API 测试**: Postman 或 Thunder Client (VS Code 插件)
- **数据库工具**: DB Browser for SQLite

---

## 健康检查端点

系统提供健康检查端点用于监控：

```
GET /api/health
```

响应示例：
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

---

## 常见问题解决方案

### 1. 后端启动失败

**症状**: 运行 `uvicorn app.main:app` 时报错

**解决方案**:
1. 检查 Python 版本是否满足要求（3.8+）
2. 检查依赖是否正确安装：`pip list`
3. 检查端口 8000 是否被占用
4. 查看终端输出的错误信息
5. 尝试删除 `data/lab_agent.db` 并重新运行 `python scripts/init_db.py create`

### 2. 数据库连接失败

**症状**: 报错显示无法连接数据库

**解决方案**:
1. 确认 `data` 目录存在
2. 检查 `DATABASE_URL` 环境变量配置
3. 确认数据库文件 `data/lab_agent.db` 有读写权限
4. 尝试重新初始化数据库

### 3. 本地嵌入模型加载失败

**症状**: 后端报错显示无法加载嵌入模型

**解决方案**:
1. 确认已安装 sentence-transformers：`pip install sentence-transformers>=2.2.0`
2. 检查网络连接（首次使用需要下载模型）
3. 检查内存是否足够
4. 尝试使用更小的模型，如 `BAAI/bge-small-zh-v1.5`
5. 查看后端终端的错误日志

### 4. API 密钥安全警告

**症状**: 启动时显示 API 密钥相关警告

**解决方案**:
1. API 密钥应该通过环境变量 `OPENAI_API_KEY` 设置
2. 不要将 API 密钥提交到版本控制
3. 检查 `config.json` 中是否包含 `openai_api_key` 字段（应该不包含）
4. 参考 `check_system_env.py` 脚本检查环境变量

### 5. 文档上传失败

**症状**: 点击上传后没有反应或显示错误

**解决方案**:
1. 检查文档格式是否支持（PDF、DOCX、DOC、XLSX、XLS、TXT、MD、PPTX 等）
2. 检查文档大小是否超过限制（默认 100MB）
3. 确认后端服务正常运行
4. 查看后端终端的错误日志
5. 尝试上传较小的测试文件

### 6. 内存溢出

**症状**: 处理大文档时出现 OOM (Out Of Memory) 错误

**解决方案**:
1. 减小 `chunk_size` 参数
2. 使用更小的嵌入模型
3. 减少 `initial_retrieve_count` 参数
4. 关闭重排序功能
5. 增加系统内存或使用云服务器

### 7. 依赖安装失败

**症状**: `pip install -r requirements.txt` 失败

**解决方案**:
1. 升级 pip：`pip install --upgrade pip`
2. 使用国内镜像源：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. 逐个安装失败的包，查看具体错误
4. 检查 Python 版本兼容性

### 8. 速率限制触发

**症状**: API 返回 429 状态码

**解决方案**:
1. 等待一段时间后重试
2. 检查是否有异常请求
3. 调整速率限制配置（修改 `rate_limit.py`）
4. 使用有效的认证 token

---

## 下一步

- 查看 [API 接口文档](../api/README.md) 了解所有可用接口
- 查看 [数据库设计文档](../database/README.md) 了解数据模型
- 查看 [前端开发文档](../frontend/README.md) 了解前端架构