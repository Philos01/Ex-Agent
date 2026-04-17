# 实验室智能助手 - 完整文档体系

欢迎使用实验室智能助手文档体系！本项目是一个基于RAG技术和React框架的智能问答系统。

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

1. **知识库管理**：支持 PDF、DOCX、TXT、MD、PPTX、CSV 等多种格式文档的上传、管理和删除
2. **文档向量化**：自动将文档切分并向量化，存储到 Chroma 向量数据库中
3. **智能问答**：基于知识库内容回答用户问题，支持流式输出和引用来源展示
4. **混合检索**：结合向量检索和 BM25 关键词检索，提升检索准确率
5. **文档摘要**：自动生成文档摘要，支持摘要级别的检索
6. **上下文管理**：智能管理对话历史，支持多轮对话
7. **用户认证**：支持用户注册、登录和权限管理
8. **嵌入模型管理**：支持本地嵌入模型和 OpenAI 云端嵌入模型切换
9. **LLM 供应商选择**：支持 OpenAI 云端和 Ollama 本地大语言模型
10. **技能系统**：支持自定义技能扩展，增强系统能力

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
│  │ API 路由  │  │ 服务层   │  │ 数据模型  │  │ 核心配置  │  │
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

#### 前端技术栈
- **前端框架**: Vue 3
- **构建工具**: Vite
- **CSS 框架**: Tailwind CSS
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **Markdown 解析**: Marked

### 项目目录结构

```
实验室Agent/
├── backend/                 # 后端代码目录
│   ├── app/                 # 应用主目录
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心配置和工具
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务服务层
│   │   ├── skills/          # 技能系统
│   │   ├── agents/          # Agent 系统
│   │   ├── utils/           # 工具函数
│   │   └── main.py          # FastAPI 应用入口
│   └── scripts/             # 脚本工具
├── frontend/                # 前端代码目录
│   ├── src/                 # 源代码
│   │   ├── components/      # 组件
│   │   ├── views/           # 页面视图
│   │   ├── router/          # 路由
│   │   ├── services/        # API 服务
│   │   ├── stores/          # Pinia 状态管理
│   │   └── main.js          # 入口文件
│   └── package.json         # npm 依赖
├── data/                    # 数据目录
│   ├── chroma/              # Chroma 向量数据库
│   ├── uploads/             # 上传的文档
│   ├── summaries/           # 文档摘要
│   └── lab_agent.db         # SQLite 数据库
├── skills/                  # 自定义技能目录
├── docs/                    # 文档目录（本目录）
└── config.json              # 项目配置文件
```

---

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 7+
- 4GB+ RAM（推荐 8GB+）
- 10GB+ 磁盘空间

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd 实验室Agent
   ```

2. **后端安装**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # 或 source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   python scripts/init_db.py
   ```

3. **前端安装**
   ```bash
   cd frontend
   npm install
   ```

4. **启动服务**
   ```bash
   # 终端 1 - 启动后端
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # 终端 2 - 启动前端
   cd frontend
   npm run dev
   ```

5. **访问应用**
   - 前端: http://localhost:5175
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/docs

详细的安装和配置说明请参考 [快速入门指南](./quickstart.md) 和 [部署指南](./deployment.md)。

---

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request！
