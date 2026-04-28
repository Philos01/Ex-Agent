# 常见问题解答 (FAQ)

本指南汇总了使用实验室智能助手过程中可能遇到的常见问题及其解决方案。

## 目录
- [安装问题](#安装问题)
- [配置问题](#配置问题)
- [使用问题](#使用问题)
- [技能系统](#技能系统)
- [性能问题](#性能问题)
- [安全相关](#安全相关)
- [其他问题](#其他问题)

---

## 安装问题

### Q1: Python 依赖安装失败怎么办？

**症状**: `pip install -r requirements.txt` 执行失败

**解决方案**:
1. 升级 pip：
   ```bash
   pip install --upgrade pip
   ```

2. 使用国内镜像源：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 逐个安装失败的包，查看具体错误信息

4. 确保 Python 版本 >= 3.8：
   ```bash
   python --version
   ```

---

### Q2: Node.js 依赖安装失败怎么办？

**症状**: `npm install` 执行失败

**解决方案**:
1. 清除缓存：
   ```bash
   npm cache clean --force
   ```

2. 删除 node_modules 和 package-lock.json 后重试：
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. 使用国内镜像源：
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install
   ```

4. 确保 Node.js 版本 >= 16

---

### Q3: 数据库初始化失败怎么办？

**症状**: 运行 `python scripts/init_db.py create` 报错

**解决方案**:
1. 确保 data 目录存在：
   ```bash
   mkdir -p data
   ```

2. 检查权限：
   ```bash
   chmod 755 data
   ```

3. 如果数据库已存在，尝试删除后重建：
   ```bash
   rm -f data/lab_agent.db
   python scripts/init_db.py create
   ```

---

### Q4: 端口被占用怎么办？

**症状**: 后端或前端启动时报端口占用错误

**解决方案**:
1. 查找占用端口的进程：
   ```bash
   # Windows
   netstat -ano | findstr :8000

   # Linux/Mac
   lsof -i :8000
   ```

2. 结束占用进程或使用其他端口启动

3. 修改后端端口：
   ```bash
   uvicorn app.main:app --port 8001
   ```

4. 修改前端端口（vite.config.js）：
   ```javascript
   server: { port: 5176 }
   ```

---

## 配置问题

### Q5: 如何配置 OpenAI API？

**解决方案**:
1. 在项目根目录创建/编辑 `.env` 文件：
   ```env
   OPENAI_API_KEY=sk-your-api-key
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

2. 在 `config.json` 中设置：
   ```json
   {
     "provider": "openai",
     "openai_chat_model": "gpt-3.5-turbo"
   }
   ```

---

### Q6: 如何使用 Ollama 本地模型？

**解决方案**:
1. 确保 Ollama 已安装并运行：
   ```bash
   ollama serve
   ```

2. 拉取模型：
   ```bash
   ollama pull qwen3:4b-instruct
   ```

3. 在 `config.json` 中配置：
   ```json
   {
     "provider": "ollama",
     "ollama_url": "http://localhost:11434",
     "ollama_model": "qwen3:4b-instruct"
   }
   ```

---

### Q7: 如何切换嵌入模型？

**解决方案**:
使用本地嵌入模型：
```json
{
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5"
}
```

使用 OpenAI 嵌入模型：
```json
{
  "embedding_mode": "openai",
  "openai_embedding_model": "text-embedding-3-small"
}
```

---

### Q8: 如何启用用户注册功能？

**解决方案**:
在 `config.json` 中设置：
```json
{
  "allow_user_registration": true
}
```

**注意**: 生产环境建议保持关闭，手动创建用户。

---

## 使用问题

### Q9: 上传的文档支持哪些格式？

**答案**: 系统支持以下文档格式：

| 格式 | 扩展名 | 说明 | 转换方式 |
|------|--------|------|----------|
| PDF | .pdf | 支持文本提取 | Marker (默认)/MarkItDown (可配置) |
| Word | .docx, .doc | 支持文本提取 | mammoth/python-docx |
| Excel | .xlsx, .xls | 支持表格转换 | MarkItDown (推荐)/openpyxl |
| 纯文本 | .txt | 直接读取 | - |
| Markdown | .md | 直接读取 | - |
| PowerPoint | .pptx | 支持文本提取 | python-pptx |

---

### Q10: 文档上传失败怎么办？

**解决方案**:
1. 检查文件大小是否超过限制（默认 100MB）
2. 检查文件格式是否支持（支持 PDF、DOCX、DOC、XLSX、XLS、TXT、MD、PPTX）
3. 检查文件是否损坏
4. 查看后端日志获取详细错误信息
5. 尝试上传较小的测试文件

---

### Q10b: 如何切换 PDF 转换方法？

**答案**: 系统支持在 Marker 和 MarkItDown 两种 PDF 转换方法之间切换。

**配置方法**:
在 `config.json` 中设置 `pdf_conversion_method` 参数：

```json
{
  "pdf_conversion_method": "marker"
}
```

或使用 MarkItDown：

```json
{
  "pdf_conversion_method": "markitdown"
}
```

**方法对比**:

| 方法 | 适用场景 | 性能要求 |
|------|---------|----------|
| Marker | 复杂公式、复杂布局、高质量需求 | 需要 GPU |
| MarkItDown | 简单文本 PDF、快速处理 | CPU 即可 |

**依赖安装**:
```bash
# Marker 方法
pip install marker

# MarkItDown 方法
pip install 'markitdown[pdf]'
```

---

### Q10c: Excel 文件转换失败怎么办？

**解决方案**:
1. 确保已安装必要的库：
   ```bash
   pip install 'markitdown[xlsx]'
   # 或
   pip install openpyxl
   ```

2. 检查 Excel 文件是否损坏，尝试用 Excel/WPS 重新保存

3. 如果是多工作表 Excel，确保每个工作表都有数据

4. 查看后端日志获取详细错误信息

5. 可以先将 Excel 导出为 CSV，再上传 CSV 文件

---

### Q11: 问答没有返回结果怎么办？

**解决方案**:
1. 确认已上传文档并完成处理
2. 检查向量库是否有数据：
   ```http
   GET /api/vector-store/status
   ```
3. 尝试使用更简单的问题测试
4. 检查后端日志是否有错误
5. 确认 OpenAI/Ollama 服务正常运行

---

### Q12: 如何查看对话历史？

**解决方案**:
1. 在前端界面左侧导航栏点击「对话」
2. 系统会自动保存对话历史到数据库
3. 可以通过 API 获取：
   ```http
   GET /api/sessions
   GET /api/sessions/{session_id}/messages
   ```

---

### Q13: 如何调整生成回答的质量？

**解决方案**:
在 `config.json` 中调整参数：

```json
{
  "temperature": 0.5,
  "top_p": 0.9,
  "max_tokens": 2048
}
```

**参数说明**:
- `temperature`: 降低值使回答更确定（0.0-0.3）
- `top_p`: 降低值使回答更集中
- `max_tokens`: 增加值允许更长的回答

---

## 技能系统

### Q14: 什么是技能系统？

**答案**: 技能系统是实验室智能助手的扩展机制，允许通过自定义技能（Skills）来增强系统的功能。每个技能可以独立执行特定任务，如搜索学术论文、查询天气等。

**内置技能**:
- `amap-weather`: 高德天气查询
- `arxiv-watcher`: ArXiv 论文搜索

---

### Q15: 如何启用技能系统？

**解决方案**:
1. 在 `skills_config.yaml` 中启用：
   ```yaml
   global:
     enabled: true

   amap-weather:
     enabled: true

   arxiv-watcher:
     enabled: true
   ```

2. 在 `config.json` 中启用技能配置：
   ```json
   {
     "skills": {
       "enabled": true,
       "arxiv_search": {
         "enabled": true,
         "max_results": 5
       }
     }
   }
   ```

---

### Q16: 如何使用天气查询技能？

**答案**: 当您询问与天气相关的问题时，系统会自动调用高德天气技能。例如：

- 「北京今天天气怎么样？」
- 「上海明天会下雨吗？」

**注意**: 需要在环境变量中配置高德 API Key：
```env
AMAP_API_KEY=your-amap-api-key
```

---

### Q17: 如何使用 ArXiv 论文搜索技能？

**答案**: 当您询问与学术论文相关的问题时，系统会自动调用 ArXiv 搜索技能。例如：

- 「帮我找一下关于 RAG 的最新论文」
- 「搜索 transformer 架构的论文」

---

### Q18: 如何开发自定义技能？

**解决方案**:
1. 在 `skills/` 目录下创建新的技能目录
2. 创建 `SKILL.md` 定义技能元数据
3. 实现技能的核心逻辑
4. 在 `skills_config.yaml` 中注册技能

详细开发指南请参考技能目录中的示例。

---

### Q19: 技能执行失败怎么办？

**解决方案**:
1. 检查技能是否已启用
2. 检查技能配置是否正确
3. 查看后端日志获取详细错误信息
4. 确认技能依赖的外部服务正常运行
5. 检查 API Key 等认证信息是否配置

---

## 性能问题

### Q20: 系统响应很慢怎么办？

**解决方案**:
1. **使用本地嵌入模型**：
   ```json
   {
     "embedding_mode": "local",
     "local_embedding_model": "BAAI/bge-small-zh-v1.5"
   }
   ```

2. **减少检索数量**：
   ```json
   {
     "top_k": 3,
     "hybrid_search": {
       "initial_retrieve_count": 10
     }
   }
   ```

3. **关闭不必要的功能**：
   ```json
   {
     "hybrid_search": { "enabled": false },
     "summary_search": { "enabled": false }
   }
   ```

4. **增加系统资源**（内存、CPU）

5. **使用更快的 LLM 模型**

---

### Q21: 内存占用过高怎么办？

**解决方案**:
1. 减小 `chunk_size` 参数
2. 使用更小的嵌入模型
3. 减少 `hybrid_search.initial_retrieve_count`
4. 关闭重排序功能
5. 限制上传文档的大小
6. 定期清理不需要的文档

---

### Q22: 向量库查询很慢怎么办？

**解决方案**:
1. 确保使用 SSD 存储向量库
2. 减少向量库中的文档数量
3. 使用更小的嵌入模型
4. 优化 ChromaDB 配置
5. 考虑使用更高效的向量数据库（如 Milvus、Qdrant）

---

## 安全相关

### Q23: 如何保护 API 密钥安全？

**解决方案**:
1. 永远不要将 `.env` 文件提交到版本控制
2. 使用环境变量而不是硬编码密钥
3. 定期轮换密钥
4. 使用密钥管理服务
5. 确保 `.gitignore` 包含 `.env` 文件

---

### Q24: 如何防止未授权访问？

**解决方案**:
1. 确保 `allow_user_registration` 在生产环境关闭
2. 使用强密码和 JWT 密钥
3. 启用 HTTPS
4. 配置 API 速率限制
5. 定期检查审计日志

---

### Q25: 如何处理敏感文档？

**解决方案**:
1. 不要上传包含敏感信息的文档
2. 使用独立的数据库实例处理敏感数据
3. 配置文档访问权限
4. 定期清理不需要的文档
5. 启用审计日志记录文档访问

---

## 其他问题

### Q26: 如何查看系统日志？

**解决方案**:
1. 后端日志直接输出到终端
2. 配置日志文件输出：
   ```python
   logging.basicConfig(
       filename='/var/log/lab_agent/app.log',
       level=logging.INFO
   )
   ```
3. 查看 API 文档中的审计日志接口

---

### Q27: 如何备份和恢复数据？

**解决方案**:
备份数据库：
```bash
# SQLite
cp data/lab_agent.db data/lab_agent.db.backup

# 或使用 sqlite3
sqlite3 data/lab_agent.db ".backup 'backup.db'"
```

备份向量库：
```bash
cp -r data/chroma data/chroma.backup
```

备份上传文件：
```bash
cp -r data/uploads data/uploads.backup
```

恢复数据：
```bash
cp data/lab_agent.db.backup data/lab_agent.db
cp -r data/chroma.backup data/chroma
```

---

### Q28: 如何升级到新版本？

**解决方案**:
1. 备份现有数据
2. 拉取最新代码：
   ```bash
   git pull origin main
   ```
3. 更新依赖：
   ```bash
   # 后端
   pip install -r requirements.txt

   # 前端
   npm install
   ```
4. 运行数据库迁移（如有）：
   ```bash
   python scripts/migrate_db.py
   ```
5. 重启服务

---

### Q29: 如何联系开发者？

**解决方案**:
- 提交 GitHub Issue
- 发送 Pull Request
- 查看项目文档
- 参与社区讨论

---

### Q30: 文档内容与实际功能不符怎么办？

**解决方案**:
1. 检查是否使用了正确版本的代码
2. 查看 API 文档（`/docs`）获取最新接口信息
3. 查看后端日志了解实际行为
4. 提交 Issue 报告文档问题

---

## 获取更多帮助

如果以上 FAQ 无法解决您的问题：

1. 查看 [完整文档](../README.md)
2. 查看 [后端开发文档](../backend/README.md)
3. 查看 [API 接口文档](../api/README.md)
4. 提交 GitHub Issue