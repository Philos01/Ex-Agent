# 实验室智能助手 - 完整文档体系

欢迎使用实验室智能助手文档体系！本项目是一个基于 RAG（检索增强生成）技术和 Vue 3 框架的智能问答系统，支持多模态文档处理、混合检索、技能扩展等高级功能。

## 文档导航

### 快速开始
- [项目概述](#项目概述)
- [快速入门指南](./quickstart.md)
- [部署指南](./deployment.md)

### 核心模块文档
- [后端开发文档](./backend/README.md)
- [前端开发文档](./frontend/README.md)
- [数据库设计文档](./database/README.md)
- [API 接口文档](./api/README.md)

### 参考资料
- [配置指南](./configuration.md)
- [常见问题解答](./faq.md)
- [贡献指南](./contributing.md)

---

## 项目概述

### 主要功能

实验室智能助手是一个功能完整的 RAG 知识库问答系统，主要功能包括：

1. **知识库管理**：支持 PDF、DOCX、DOC、XLSX、XLS、TXT、MD、PPTX 等多种格式文档的上传、管理和删除，其中 Excel 文件使用 MarkItDown 转换为 Markdown 格式存储
2. **文档向量化**：自动将文档切分并向量化，存储到 Chroma 向量数据库中
3. **智能问答**：基于知识库内容回答用户问题，支持流式输出和引用来源展示
4. **混合检索**：结合向量检索和 BM25 关键词检索，配合重排序模型提升检索准确率
5. **双层检索**：结合摘要检索和内容检索，实现摘要级别和内容级别的多层次检索
6. **文档摘要**：自动生成文档摘要，支持摘要级别的检索
7. **上下文管理**：智能管理对话历史，支持多轮对话
8. **用户认证**：支持用户注册、登录和基于 JWT 的权限管理
9. **嵌入模型管理**：支持本地嵌入模型和 OpenAI 云端嵌入模型切换
10. **LLM 供应商选择**：支持 OpenAI 云端模型和 Ollama 本地大语言模型
11. **技能系统**：支持自定义技能扩展，包括 ArXiv 论文搜索、高德天气查询等
12. **速率限制**：内置登录和 API 速率限制，保护系统安全
13. **思考步骤显示**：支持启用思考步骤显示，便于理解 AI 推理过程
14. **ReAct 多步推理**：支持启用 ReAct 模式进行复杂多步推理

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层 (Vue 3)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 聊天页面  │  │ 上传页面  │  │ 设置页面  │  │ 登录页面  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        后端层 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ API v1   │  │ 服务层   │  │ 数据模型  │  │ 核心配置  │  │
│  │ 路由     │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Agent    │  │ 技能系统  │  │ 审计日志  │  │ 速率限制  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  SQLite 数据库 │    │ Chroma 向量库  │    │   文件存储    │
│  (用户/会话)   │    │  (文档向量)    │    │ (上传文档/摘要)│
└───────────────┘    └───────────────┘    └───────────────┘
```

### 技术栈

#### 后端技术栈
- **Web 框架**: FastAPI >= 0.104.0
- **ASGI 服务器**: Uvicorn >= 0.24.0
- **数据库 ORM**: SQLAlchemy >= 2.0.0
- **向量数据库**: ChromaDB >= 0.4.0
- **嵌入模型**: Sentence-Transformers >= 2.2.0
- **LLM 集成**: OpenAI SDK >= 1.0.0, Ollama
- **文件处理**: pdfplumber, python-docx, mammoth, openpyxl
- **文本检索**: Jieba, BM25
- **深度学习**: PyTorch >= 2.0.0, Transformers >= 4.35.0
- **认证**: python-jose, bcrypt
- **速率限制**: Flask-Limiter (适配 FastAPI)

#### 前端技术栈
- **前端框架**: Vue 3 >= 3.4.0
- **构建工具**: Vite >= 5.0.0
- **CSS 框架**: Tailwind CSS >= 4.2.2
- **状态管理**: Pinia >= 2.1.0
- **路由**: Vue Router >= 4.2.0
- **HTTP 客户端**: Axios >= 1.6.0
- **Markdown 解析**: Marked >= 18.0.0

### 项目目录结构

```
实验室Agent/
├── backend/                     # 后端代码目录
│   ├── app/                     # 应用主目录
│   │   ├── api/                 # API 路由 (v1 版本路由)
│   │   │   ├── v1/             # v1 版本 API
│   │   │   │   ├── auth.py     # 认证接口
│   │   │   │   ├── routes.py   # 主要业务 API
│   │   │   │   ├── sessions.py # 会话管理 API
│   │   │   │   └── skills.py   # 技能 API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关
│   │   │   ├── routes.py       # 主要业务路由
│   │   │   ├── sessions.py     # 会话管理
│   │   │   └── skills.py       # 技能管理
│   │   ├── core/               # 核心配置和工具
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── dependencies.py # 依赖注入
│   │   │   ├── logging_config.py # 日志配置
│   │   │   └── rate_limit.py   # 速率限制
│   │   ├── models/             # 数据模型
│   │   │   ├── base.py         # 基础模型
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── session.py      # 会话模型
│   │   │   ├── message.py      # 消息模型
│   │   │   ├── document.py     # 文档模型
│   │   │   ├── audit_log.py    # 审计日志模型
│   │   │   ├── permission.py   # 权限模型
│   │   │   ├── role_permission.py # 角色权限关联
│   │   │   └── schemas.py      # Pydantic 模式
│   │   ├── services/           # 业务服务层
│   │   │   ├── auth.py         # 认证服务
│   │   │   ├── ingest.py       # 文档处理服务
│   │   │   ├── qa.py           # 问答服务
│   │   │   ├── vector_store.py # 向量存储服务
│   │   │   ├── embedding.py    # 嵌入服务
│   │   │   ├── hybrid_search.py # 混合检索服务
│   │   │   ├── bm25_search.py  # BM25 检索服务
│   │   │   ├── rerank.py       # 重排序服务
│   │   │   ├── query_rewrite.py # 查询重写服务
│   │   │   ├── document_summary.py # 文档摘要服务
│   │   │   ├── summary_store.py # 摘要存储服务
│   │   │   ├── two_layer_search.py # 双层检索服务
│   │   │   ├── context_manager.py # 上下文管理服务
│   │   │   └── audit.py        # 审计服务
│   │   ├── skills/             # 技能系统
│   │   │   ├── base.py         # 技能基类
│   │   │   ├── discovery.py    # 技能发现
│   │   │   ├── metadata_parser.py # 元数据解析
│   │   │   ├── skill_executor.py # 技能执行器
│   │   │   ├── skill_manager.py # 技能管理器
│   │   │   └── skill_selector.py # 技能选择器
│   │   ├── agents/             # Agent 系统
│   │   │   ├── exceptions.py   # 异常定义
│   │   │   ├── memory.py       # 记忆管理
│   │   │   ├── output_parser.py # 输出解析器
│   │   │   ├── prompt_engine.py # 提示词引擎
│   │   │   └── react_agent.py  # ReAct Agent
│   │   ├── utils/              # 工具函数
│   │   │   ├── exceptions.py   # 异常定义
│   │   │   └── file_utils.py   # 文件工具
│   │   └── main.py             # FastAPI 应用入口
│   └── scripts/                 # 脚本工具
│       ├── check_paths.py
│       ├── check_root.py
│       ├── check_vector_store.py
│       ├── docx2markdown.py
│       ├── init_db.py          # 数据库初始化
│       ├── manage_users.py     # 用户管理
│       ├── migrate_db.py        # 数据库迁移
│       ├── pdf2markdown.py
│       └── skill_deployer.py   # 技能部署
├── frontend/                    # 前端代码目录
│   ├── src/                     # 源代码
│   │   ├── components/          # 组件
│   │   │   ├── gen-ui/         # 通用 UI 组件
│   │   │   ├── Chat.jsx        # 聊天组件
│   │   │   ├── Settings.jsx    # 设置组件
│   │   │   ├── Uploads.jsx      # 上传组件
│   │   │   └── ErrorBoundary.jsx # 错误边界
│   │   ├── views/              # 页面视图
│   │   │   ├── ChatView.vue    # 聊天页面
│   │   │   ├── LoginView.vue   # 登录页面
│   │   │   ├── SettingsView.vue # 设置页面
│   │   │   └── UploadsView.vue # 上传页面
│   │   ├── router/             # 路由
│   │   ├── services/           # API 服务
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── App.vue             # 根组件
│   │   ├── App.jsx             # React 根组件
│   │   └── main.js             # 入口文件
│   └── package.json            # npm 依赖
├── skills/                      # 自定义技能目录
│   ├── amap-weather/           # 高德天气技能
│   │   ├── scripts/
│   │   ├── references/
│   │   └── SKILL.md
│   └── arxiv-watcher/          # ArXiv 搜索技能
│       ├── scripts/
│       └── SKILL.md
├── data/                        # 数据目录
│   ├── chroma/                 # Chroma 向量数据库
│   ├── uploads/                # 上传的文档
│   ├── summaries/              # 文档摘要
│   └── lab_agent.db            # SQLite 数据库
├── docs/                        # 文档目录（本目录）
├── config.json                  # 项目配置文件
├── skills_config.yaml           # 技能配置文件
└── .env.example                 # 环境变量示例
```

---

## 快速开始

### 环境要求

- Python 3.8+ (推荐 3.10+)
- Node.js 16+ (推荐 18+)
- npm 7+
- 4GB+ RAM（推荐 8GB+）
- 10GB+ 磁盘空间

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Philos01/Ex-Agent.git
   cd 实验室Agent
   ```

2. **后端安装**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # 或 source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   python scripts/init_db.py create
   ```

3. **前端安装**
   ```bash
   cd frontend
   npm install
   ```

4. **配置环境变量**

   复制 `.env.example` 为 `.env` 并配置：
   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件，填入您的 API 密钥：
   ```env
   OPENAI_API_KEY=your-openai-api-key
   SECRET_KEY=your-secret-key-change-this-in-production
   ```

5. **启动服务**
   ```bash
   # 终端 1 - 启动后端
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # 终端 2 - 启动前端
   cd frontend
   npm run dev
   ```

6. **访问应用**
   - 前端: http://localhost:5175
   - 后端 API: http://localhost:8000
   - API 文档 (Swagger): http://localhost:8000/docs
   - API 文档 (ReDoc): http://localhost:8000/redoc

详细的安装和配置说明请参考 [快速入门指南](./quickstart.md) 和 [部署指南](./deployment.md)。

---

## API 版本说明

本系统提供两个版本的 API：

- **v1 API** (`/api/v1/*`) - 最新版本的 API 接口
- **原始 API** (`/api/*`) - 保持向后兼容的原始接口

新项目建议使用 v1 API。

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request！