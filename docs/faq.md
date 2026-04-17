# 常见问题解答 (FAQ)

## 目录
- [安装与配置](#安装与配置)
- [后端问题](#后端问题)
- [前端问题](#前端问题)
- [数据库问题](#数据库问题)
- [RAG 功能问题](#rag-功能问题)
- [性能优化](#性能优化)
- [安全相关](#安全相关)

---

## 安装与配置

### Q: 如何检查 Python 版本是否符合要求？

**A**: 运行以下命令检查 Python 版本：
```bash
python --version
# 或
python3 --version
```

要求 Python 3.8 或更高版本。

---

### Q: 如何安装特定版本的 Python？

**A**: 
- **Windows**: 从 [python.org](https://www.python.org/downloads/) 下载安装
- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install python3.10 python3.10-venv python3.10-dev
  ```
- **macOS**: 使用 Homebrew
  ```bash
  brew install python@3.10
  ```

---

### Q: pip 安装依赖很慢怎么办？

**A**: 使用国内镜像源：
```bash
# 临时使用
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

其他可用镜像源：
- 阿里云: https://mirrors.aliyun.com/pypi/simple/
- 中科大: https://pypi.mirrors.ustc.edu.cn/simple/
- 豆瓣: https://pypi.douban.com/simple/

---

### Q: config.json 文件在哪里？如何创建？

**A**: config.json 位于项目根目录。首次运行后端时会自动创建。你也可以手动复制 `.env.example` 或从默认配置创建：

```json
{
  "provider": "openai",
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "temperature": 0.7,
  "top_k": 5
}
```

---

### Q: 如何配置 OpenAI API 密钥？

**A**: API 密钥通过环境变量配置，不要直接写在 config.json 中：

**Windows PowerShell**:
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**Windows CMD**:
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Linux/Mac**:
```bash
export OPENAI_API_KEY=your-api-key-here
```

**永久配置**：创建 `.env` 文件在项目根目录：
```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```

---

## 后端问题

### Q: 后端启动失败，提示 "No module named 'xxx'"

**A**: 
1. 确认虚拟环境已激活
2. 重新安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 检查 requirements.txt 文件是否完整
4. 尝试逐个安装失败的包

---

### Q: 端口 8000 被占用怎么办？

**A**: 
1. 查找占用进程：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```
2. 结束占用进程，或使用其他端口启动：
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

---

### Q: 如何查看后端日志？

**A**: 
- 开发模式：日志直接输出到终端
- 生产模式：查看配置的日志文件，或使用 systemd 日志：
  ```bash
  sudo journalctl -u lab-agent-backend -f
  ```

---

### Q: CORS 错误怎么办？

**A**: 后端已配置允许所有来源的 CORS。如果仍有问题：
1. 检查前端 API 地址是否正确
2. 确认后端服务正在运行
3. 检查防火墙设置

---

## 前端问题

### Q: 前端无法连接后端

**A**: 
1. 确认后端服务正在运行
2. 检查 `vite.config.js` 中的代理配置：
   ```javascript
   proxy: {
     '/api': {
       target: 'http://localhost:8000',
       changeOrigin: true
     }
   }
   ```
3. 检查浏览器控制台的错误信息
4. 确认端口号正确

---

### Q: npm install 失败怎么办？

**A**: 
1. 清除 npm 缓存：
   ```bash
   npm cache clean --force
   ```
2. 删除 `node_modules` 和 `package-lock.json`，重新安装
3. 使用国内镜像：
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install
   ```

---

### Q: 前端页面显示空白

**A**: 
1. 检查浏览器控制台是否有错误
2. 确认 `npm run dev` 成功启动
3. 检查路由配置
4. 清除浏览器缓存，硬刷新页面（Ctrl+Shift+R）

---

### Q: 如何构建生产版本？

**A**:
```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录，可以部署到 Nginx 等 Web 服务器。

---

## 数据库问题

### Q: SQLite 数据库文件在哪里？

**A**: 默认位置：
```
data/lab_agent.db
```

可以通过 `DATABASE_URL` 环境变量修改。

---

### Q: 如何重置数据库？

**A**: 
1. 停止后端服务
2. 删除数据库文件：
   ```bash
   rm data/lab_agent.db
   ```
3. 重新初始化：
   ```bash
   cd backend/scripts
   python init_db.py create
   ```

---

### Q: 数据库锁定错误 (database is locked)

**A**: 
1. 确认没有其他进程正在访问数据库
2. 增加超时时间（在 config.py 中）：
   ```python
   engine = create_engine(
       DATABASE_URL,
       connect_args={"check_same_thread": False, "timeout": 30}
   )
   ```
3. 考虑使用 PostgreSQL/MySQL 替代 SQLite（生产环境推荐）

---

### Q: 如何备份数据库？

**A**:
```bash
# 简单复制
cp data/lab_agent.db data/lab_agent.db.backup

# 使用 SQLite 命令
sqlite3 data/lab_agent.db ".backup 'data/lab_agent.db.backup'"
```

---

## RAG 功能问题

### Q: 文档上传后无法检索到

**A**: 
1. 确认文档格式支持（PDF, DOCX, TXT, MD 等）
2. 检查后端日志，看是否有处理错误
3. 尝试重新上传文档
4. 检查向量库状态：
   ```
   GET /api/vector-store/status
   ```

---

### Q: 检索结果不准确怎么办？

**A**: 
1. 调整 `top_k` 参数，增加检索数量
2. 启用混合检索：
   ```json
   {
     "hybrid_search": {
       "enabled": true,
       "bm25_weight": 0.5,
       "embedding_weight": 0.5
     }
   }
   ```
3. 调整文档分块大小：
   ```json
   {
     "chunk_size": 1000,
     "chunk_overlap": 200
   }
   ```
4. 启用查询重写和重排序
5. 尝试更好的嵌入模型

---

### Q: 回答质量不高怎么办？

**A**: 
1. 调整生成参数：
   - 降低 `temperature` 使回答更确定
   - 增加 `max_tokens` 获得更长回答
2. 提供更多相关文档
3. 优化问题表述
4. 尝试使用更好的 LLM 模型
5. 检查检索到的上下文是否相关

---

### Q: 本地嵌入模型下载很慢怎么办？

**A**: 
1. 确保网络连接稳定
2. 使用镜像源（如 ModelScope）
3. 预先下载模型到本地目录，配置 `local_model_cache_dir`
4. 使用更小的模型（如 `BAAI/bge-small-zh-v1.5`）

---

### Q: 如何切换到 Ollama 本地模型？

**A**: 
1. 安装并启动 Ollama：https://ollama.ai
2. 拉取模型：
   ```bash
   ollama pull llama2
   ```
3. 修改配置：
   ```json
   {
     "provider": "ollama",
     "ollama_url": "http://localhost:11434",
     "ollama_model": "llama2"
   }
   ```

---

## 性能优化

### Q: 系统响应很慢怎么办？

**A**: 
1. **后端优化**：
   - 使用更快的嵌入模型
   - 减少 `top_k` 和 `initial_retrieve_count`
   - 关闭不必要的功能（重排序、查询重写）
   - 使用 Gunicorn + 多 worker

2. **前端优化**：
   - 启用生产模式构建
   - 配置 CDN 加速静态资源

3. **硬件升级**：
   - 增加内存
   - 使用 SSD
   - 使用 GPU 加速（如有）

---

### Q: 内存占用过高怎么办？

**A**: 
1. 使用更小的嵌入模型
2. 减少分块大小
3. 减少 `initial_retrieve_count`
4. 关闭重排序功能
5. 限制同时处理的文档数量

---

### Q: 如何处理大量文档？

**A**: 
1. 使用更好的向量数据库（如 Qdrant, Weaviate）
2. 实现文档分批处理
3. 使用增量索引
4. 考虑分布式部署

---

## 安全相关

### Q: API 密钥安全吗？

**A**: 
- API 密钥通过环境变量读取，不保存到配置文件
- 不要将 `.env` 文件提交到版本控制
- 定期轮换 API 密钥
- 生产环境使用密钥管理服务

---

### Q: 如何启用用户认证？

**A**: 
1. 修改配置启用注册：
   ```json
   {
     "allow_user_registration": true
   }
   ```
2. 或使用 `manage_users.py` 脚本创建用户：
   ```bash
   cd backend/scripts
   python manage_users.py create --username admin --email admin@example.com --password yourpassword --role admin
   ```

---

### Q: 生产环境需要注意哪些安全事项？

**A**: 
1. 使用 HTTPS
2. 修改默认 `SECRET_KEY`
3. 启用防火墙
4. 定期更新依赖
5. 配置日志监控
6. 使用非 root 用户运行服务
7. 限制文件上传大小和类型
8. 配置速率限制

---

### Q: 如何防止 CSRF 攻击？

**A**: 
- 使用 SameSite cookies
- 验证 Origin/Referer 头部
- 使用 CSRF token（目前主要依赖 JWT 认证）

---

## 其他问题

### Q: 如何贡献代码？

**A**: 
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

详细指南请查看项目的贡献指南（如有）。

---

### Q: 项目使用什么许可证？

**A**: 本项目使用 MIT 许可证。详见 LICENSE 文件。

---

### Q: 如何获取帮助？

**A**: 
1. 查看本文档和其他文档
2. 查看项目的 Issue 列表
3. 提交新的 Issue
4. 联系项目维护者

---

### Q: 有计划支持更多功能吗？

**A**: 项目持续迭代中，可能的规划包括：
- 更多文档格式支持
- 更多 LLM 供应商集成
- 多语言支持
- 协作功能
- 更多自定义技能

欢迎提出 Feature Request！

---

## 下一步

如果以上解答无法解决您的问题：
1. 查看详细的模块文档
2. 检查后端日志中的错误信息
3. 在 GitHub 提交 Issue 并提供详细信息
