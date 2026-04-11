
# 实验室智能助手 — 完整项目（后端 + 前端）

这是一个基于 FastAPI 和 Vue.js 的智能助手项目，提供知识库管理、文档向量化、聊天交互等功能。项目采用现代化的技术栈，包括后端的 FastAPI、Chroma 向量数据库，以及前端的 Vue 3、Vite 和 Tailwind CSS。

**注意**：本仓库提供 Windows 与 Linux 的启动脚本；不包含 macOS 专用脚本。

## 目录结构

- **backend/**: 后端代码（FastAPI）
- **frontend/**: 前端代码（Vite + Vue 3 + Tailwind CSS）
- **data/**: 数据存储目录（向量库、上传文件等）
- **requirements.txt**: 后端依赖
- **config.json**: 项目配置文件
- **README.md**: 本说明
- **EMBEDDING_SETUP_GUIDE.md**: 嵌入模型本地部署指南
- **.gitignore**: Git 忽略文件配置

## 系统要求

- Python 3.8+
- Node.js 16+
- npm 7+
- 4GB+ RAM（推荐 8GB+ 以获得更好性能）

## 快速开始

### 1. 安装后端依赖并启动后端

#### Linux

```bash
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用仓库根目录提供的一键脚本：

```bash
./start_backend.sh
```

#### Windows PowerShell

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用一键脚本：

```powershell
start_backend.bat
```

### 2. 安装前端依赖并启动开发服务器

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 http://localhost:5175/。

## 功能说明

### 1. 知识库管理

- **文档上传**：支持 PDF、DOCX、TXT、MD、PPTX、CSV 等格式的文档上传
- **文档列表**：查看已上传的文档列表，包括文件名、大小、上传日期和状态
- **文档删除**：删除不需要的文档
- **向量文档统计**：实时显示向量化文档数量
- **内存占用统计**：实时显示内存占用情况

### 2. 聊天功能

- **智能问答**：基于知识库内容回答问题
- **新建分析**：创建新的聊天会话
- **引用源**：显示回答引用的文档来源

### 3. 嵌入模型管理

- **本地/云端模式切换**：支持本地嵌入模型和 OpenAI 云端嵌入模型
- **推荐模型列表**：提供 5 个高质量本地嵌入模型推荐
- **模型状态监控**：实时查看当前嵌入模型状态

### 4. 系统设置

- **LLM 供应商选择**：支持 OpenAI 云端和 Ollama 本地
- **API 凭证配置**：设置 API 终端 URL、密钥和组织 ID
- **RAG 与神经元调优**：调整分块大小、重叠度和温度参数

## 使用指南

### 1. 知识库管理

1. 点击左侧导航栏中的「知识库」选项
2. 点击「选择文件」按钮选择要上传的文档
3. 选择文件后，点击「同步知识库」按钮开始上传和向量化
4. 上传完成后，文档会显示在知识库列表中
5. 可以点击文档右侧的删除按钮删除不需要的文档

### 2. 聊天功能

1. 点击左侧导航栏中的「对话」选项
2. 在输入框中输入问题，点击发送按钮
3. 系统会基于知识库内容生成回答，并显示引用的文档来源
4. 点击左侧的「新建分析」按钮可以创建新的聊天会话

### 3. 嵌入模型管理（新增功能）

#### 切换嵌入模式

**方式 1：通过配置文件
1. 打开 `config.json` 文件
2. 修改 `embedding_mode` 为 `"local"` 或 `"openai"`
3. 重启后端服务
4. 重置向量库并重新上传文档（建议）

**方式 2：通过 API**
```bash
# 获取推荐模型列表
GET /api/embedding/models/recommended

# 获取当前状态
GET /api/embedding/status

# 切换模式
POST /api/embedding/mode
{
  "mode": "local",
  "reset_collection": true
}
```

详细说明请参考 `EMBEDDING_SETUP_GUIDE.md`。

### 4. 系统设置

1. 点击左侧导航栏中的「设置」选项
2. 选择 LLM 供应商（OpenAI 云端或 Ollama 本地）
3. 配置 API 凭证（API 终端 URL、密钥和组织 ID）
4. 调整 RAG 与神经元调优参数（分块大小、重叠度和温度）
5. 点击「应用更改」按钮保存配置

## 配置说明

### 后端配置

后端配置文件位于项目根目录的 `config.json`，包含以下配置项：

```json
{
  "provider": "ollama",
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "local_model_cache_dir": "",
  "openai_api_key": "your-api-key",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_embedding_model": "text-embedding-3-small",
  "openai_chat_model": "gpt-3.5-turbo",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "Qwen3.5:2B",
  "chunk_size": 1500,
  "chunk_overlap": 100,
  "temperature": 0.7,
  "top_k": 5,
  "top_p": 0.9,
  "max_tokens": 2048,
  "presence_penalty": 0,
  "frequency_penalty": 0,
  "max_history": 10,
  "upload_max_size": 104857600
}
```

**主要配置项说明：
- **provider**：LLM 供应商（"openai" 或 "ollama"）
- **embedding_mode**：嵌入模式（"local" 或 "openai"）
- **local_embedding_model**：本地嵌入模型名称（Hugging Face 模型 ID）
- **local_model_cache_dir**：模型缓存目录（可选）
- **openai_api_key**：OpenAI API 密钥
- **openai_base_url**：OpenAI API 基础 URL
- **openai_embedding_model**：OpenAI 嵌入模型
- **openai_chat_model**：OpenAI 聊天模型
- **ollama_url**：Ollama 服务地址
- **ollama_model**：Ollama 模型名称
- **chunk_size**：分块大小
- **chunk_overlap**：重叠度
- **temperature**：温度参数

### 前端配置

前端配置文件位于 `frontend/vite.config.js`，主要配置代理服务器以解决跨域问题：

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5175,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
        proxyTimeout: 600000,
        ws: true
      }
    }
  }
})
```

## 推荐的本地嵌入模型

### 1. BAAI/bge-small-zh-v1.5 ⭐ 强烈推荐
- **描述**：中文小型嵌入模型，适合普通硬件，语义理解能力良好
- **维度**：512
- **语言**：中文
- **优势**：模型体积小、加载速度快、内存占用低（4GB RAM 即可）

### 2. BAAI/bge-base-zh-v1.5
- **描述**：中文基础嵌入模型，性能更好，需要更多内存
- **维度**：768
- **语言**：中文

### 3. shibing624/text2vec-base-chinese
- **描述**：轻量级中文文本嵌入模型
- **维度**：768
- **语言**：中文

### 4. all-MiniLM-L6-v2
- **描述**：通用小型多语言嵌入模型，速度快
- **维度**：384
- **语言**：多语言

### 5. m3e-base
- **描述**：M3E中文嵌入模型，在多项任务上表现优秀
- **维度**：768
- **语言**：中文

详细的嵌入模型使用指南请参考 `EMBEDDING_SETUP_GUIDE.md`。

## 故障排除

### 1. 后端启动失败

- 检查 Python 版本是否满足要求（3.8+）
- 检查依赖是否正确安装：`pip list`
- 检查端口 8000 是否被占用
- 查看终端输出的错误信息

### 2. 前端启动失败

- 检查 Node.js 版本是否满足要求（16+）
- 检查依赖是否正确安装：`npm list`
- 检查端口 5175 是否被占用

### 3. 文档上传失败

- 检查文档格式是否支持
- 检查文档大小是否超过限制（默认 100MB）
- 检查后端服务是否正常运行
- 查看终端输出的错误信息

### 4. 聊天功能无响应

- 检查后端服务是否正常运行
- 检查 API 凭证是否正确配置
- 检查知识库是否有文档
- 检查 LLM 供应商是否可用

### 5. 设置保存失败

- 检查后端服务是否正常运行
- 检查配置格式是否正确
- 检查 config.json 文件权限

### 6. 本地嵌入模型加载失败

- 确保已安装 sentence-transformers：`pip install sentence-transformers&gt;=2.2.0`
- 检查网络连接（首次使用需要下载模型）
- 检查内存是否足够
- 查看后端终端的错误日志

### 7. 切换嵌入模型后搜索结果异常

- **重要**：切换嵌入模型或模式后，向量维度可能改变，必须重置向量库
- 重置后重新上传文档
- 检查 config.json 中的配置是否正确

## 技术栈

### 后端

- **FastAPI**：高性能 Python Web 框架
- **Chroma**：轻量级向量数据库
- **Sentence-Transformers**：本地嵌入模型支持
- **OpenAI**：云端大语言模型
- **Ollama**：本地大语言模型
- **SQLAlchemy**：数据库 ORM

### 前端

- **Vue 3**：JavaScript 前端框架
- **Vite**：现代化前端构建工具
- **Tailwind CSS**：实用优先的 CSS 框架
- **Material Symbols**：Google 图标库
- **Axios**：HTTP 请求库

## 下一步

- 完善错误处理和用户反馈
- 增加更多文档格式支持
- 优化向量化性能
- 增加用户认证和权限管理
- 添加更多数据分析和可视化功能
- 支持更多本地嵌入模型
- 增加模型性能对比工具

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！
