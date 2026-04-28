# 快速入门指南

本指南将帮助您在 10 分钟内快速启动并运行实验室智能助手。

## 前置条件

在开始之前，请确保您已安装：

- Python 3.8 或更高版本（推荐 3.10+）
- Node.js 16 或更高版本（推荐 18+）
- Git（可选，用于克隆项目）
- 4GB+ RAM（推荐 8GB+）

---

## 第一步：获取项目

### 方式 1：克隆仓库（推荐）

```bash
git clone <repository-url>
cd 实验室Agent
```

### 方式 2：下载 ZIP

从 GitHub 下载项目 ZIP 并解压。

---

## 第二步：配置后端

### 1. 进入后端目录

```bash
cd backend
```

### 2. 创建虚拟环境

**Windows PowerShell**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/Mac**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/lab_agent.db

# JWT 密钥（生产环境请修改为强密钥）
SECRET_KEY=your-secret-key-change-this-in-production-please

# OpenAI 配置（如使用）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 5. 初始化数据库

```bash
cd scripts
python init_db.py create
cd ..
```

### 6. 启动后端服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 http://localhost:8000 启动。

---

## 第三步：配置前端

### 1. 打开新终端，进入前端目录

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 启动前端开发服务器

```bash
npm run dev
```

前端将在 http://localhost:5175 启动。

---

## 第四步：访问应用

1. 在浏览器中打开 http://localhost:5175
2. 查看 API 文档：http://localhost:8000/docs

---

## 第五步：创建管理员账户

默认情况下，用户注册功能是关闭的。您需要手动创建管理员账户：

```bash
cd backend/scripts
python manage_users.py create --username admin --email admin@example.com --password yourpassword --role admin
```

然后使用管理员账户登录前端。

---

## 第六步：上传文档测试

1. 点击左侧导航栏的「知识库」
2. 点击「选择文件」，选择一个或多个文档（支持 PDF、DOCX、TXT、MD 等格式）
3. 点击「同步知识库」开始上传和处理
4. 等待处理完成

---

## 第七步：开始对话

1. 点击左侧导航栏的「对话」
2. 在输入框中输入问题，例如：
   - 「请总结一下上传的文档」
   - 「这篇论文的主要贡献是什么？」
3. 点击发送按钮，等待系统回答
4. 查看回答和引用的文档来源

---

## 常用操作

### 切换 LLM 供应商

系统支持 OpenAI 和 Ollama 两种 LLM 供应商。可以通过修改 `config.json` 或在设置页面切换：

**使用 Ollama**:
```json
{
  "provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "ollama_model": "qwen3:4b-instruct"
}
```

### 切换嵌入模式

系统支持本地嵌入模型和 OpenAI 嵌入模型：

**使用本地嵌入模型**:
```json
{
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5"
}
```

**使用 OpenAI 嵌入模型**:
```json
{
  "embedding_mode": "openai",
  "openai_embedding_model": "text-embedding-3-small"
}
```

### 启用技能系统

技能系统允许扩展系统能力，如 ArXiv 论文搜索、高德天气查询等。

在 `skills_config.yaml` 中启用技能：
```yaml
global:
  enabled: true

amap-weather:
  enabled: true

arxiv-watcher:
  enabled: true
```

---

## 故障排除

### 后端无法启动

1. 检查 Python 版本是否满足要求（3.8+）
2. 检查依赖是否正确安装
3. 检查端口 8000 是否被占用

### 前端无法连接后端

1. 确认后端服务正在运行
2. 检查 `vite.config.js` 中的代理配置
3. 检查浏览器控制台的错误信息

### 文档处理失败

1. 检查文档格式是否支持
2. 检查文档大小是否超过限制
3. 查看后端终端的错误日志

详细问题排查请查看 [常见问题解答](./faq.md)。

---

## 下一步

- 阅读 [配置指南](./configuration.md) 了解如何自定义配置
- 阅读 [后端开发文档](./backend/README.md) 了解后端架构
- 阅读 [前端开发文档](./frontend/README.md) 了解前端架构
- 阅读 [部署指南](./deployment.md) 了解如何部署到生产环境