# 贡献指南

感谢您对实验室智能助手项目的关注！我们欢迎各种形式的贡献，包括但不限于代码提交、文档改进、问题报告和功能建议。

## 目录
- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题报告](#问题报告)
- [功能建议](#功能建议)

---

## 行为准则

我们希望所有参与者都能遵守以下行为准则：

1. **尊重他人** - 尊重所有参与者的意见和贡献
2. **包容性** - 欢迎不同背景和经验水平的贡献者
3. **专业性** - 保持专业和友好的交流态度
4. **建设性** - 提供建设性的反馈和批评

---

## 如何贡献

### 贡献类型

我们欢迎以下类型的贡献：

- **代码提交** - 修复 Bug、实现新功能、性能优化
- **文档改进** - 完善文档、修复错误、翻译文档
- **问题报告** - 报告 Bug、提供问题复现步骤
- **功能建议** - 提出新功能想法和改进建议
- **代码审查** - 审查其他贡献者的代码

---

## 开发环境设置

### 1. Fork 仓库

点击 GitHub 仓库页面右上角的 "Fork" 按钮。

### 2. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/实验室Agent.git
cd 实验室Agent
```

### 3. 添加上游仓库

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/实验室Agent.git
```

### 4. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 5. 设置开发环境

**后端**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

**前端**:
```bash
cd frontend
npm install
```

---

## 代码规范

### Python 代码规范

遵循 PEP 8 规范：

- 使用 4 空格缩进
- 行长度限制在 100 字符以内
- 使用有意义的变量和函数命名
- 添加必要的文档字符串

**示例**:
```python
def calculate_similarity(query_embedding: List[float], doc_embedding: List[float]) -> float:
    """
    计算查询和文档之间的余弦相似度。

    Args:
        query_embedding: 查询的嵌入向量
        doc_embedding: 文档的嵌入向量

    Returns:
        余弦相似度分数，范围在 0-1 之间
    """
    dot_product = sum(q * d for q, d in zip(query_embedding, doc_embedding))
    query_norm = math.sqrt(sum(q ** 2 for q in query_embedding))
    doc_norm = math.sqrt(sum(d ** 2 for d in doc_embedding))

    if query_norm == 0 or doc_norm == 0:
        return 0.0

    return dot_product / (query_norm * doc_norm)
```

### JavaScript/Vue 代码规范

遵循 ESLint 配置规则：

- 使用有意义的变量和函数命名
- 组件文件使用 PascalCase
- 工具函数使用 camelCase
- 添加必要的注释

**示例**:
```javascript
export async function fetchDocuments(token) {
  try {
    const response = await api.get('/documents', {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  } catch (error) {
    console.error('Failed to fetch documents:', error)
    throw error
  }
}
```

### Vue 组件规范

```vue
<template>
  <div class="component-name">
    <!-- 组件内容 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update', 'delete'])

const isLoading = ref(false)

const formattedTitle = computed(() => {
  return props.title.trim()
})

onMounted(() => {
  initializeComponent()
})
</script>

<style scoped>
.component-name {
  padding: 1rem;
}
</style>
```

---

## 提交规范

### 提交信息格式

使用 Angular 提交规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (Type)

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更改 |
| style | 代码格式（不影响功能） |
| refactor | 重构（不影响功能） |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 范围 (Scope)

表示修改的范围，例如：
- `api` - API 接口
- `auth` - 认证相关
- `frontend` - 前端相关
- `backend` - 后端相关
- `docs` - 文档相关

### 示例

```
feat(auth): 添加用户注册功能

添加了用户注册 API 接口和前端表单验证

- 添加 /api/auth/register 端点
- 添加前端注册表单组件
- 添加表单验证规则

Closes #123
```

```
fix(vector): 修复向量检索返回空结果的问题

当向量库为空时，检索接口返回空列表而不是错误

- 添加空检查逻辑
- 添加单元测试
```

---

## Pull Request 流程

### 1. 确保代码通过测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端构建检查
cd frontend
npm run build
```

### 2. 提交 PR

1. 推送分支到您的 Fork：
   ```bash
   git push origin feature/your-feature-name
   ```

2. 在 GitHub 上创建 Pull Request

3. 填写 PR 模板

### 3. PR 模板

```markdown
## 描述
<!-- 请简要描述您的更改 -->

## 类型
- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 文档更新 (docs)
- [ ] 代码重构 (refactor)
- [ ] 性能优化 (perf)
- [ ] 测试相关 (test)
- [ ] 其他 (chore)

## 影响的范围
<!-- 请说明更改影响的模块 -->

## 是否关闭 Issue
<!-- 如果有关联的 Issue，请说明 "Closes #xxx" -->

## 测试步骤
<!-- 请提供测试您更改的步骤 -->
1.
2.
3.

## 截图（如果适用）
<!-- 如果有 UI 更改，请提供截图 -->
```

### 4. 代码审查

- 响应审查反馈
- 不要在 PR 中引入不相关的更改
- 确保所有测试通过

### 5. 合并

合并前需要：
- 至少 1 人审查通过
- 所有测试通过
- 没有冲突

---

## 问题报告

### Bug 报告模板

```markdown
## Bug 描述
<!-- 请简洁清晰地描述 Bug -->

## 复现步骤
<!-- 请提供详细的复现步骤 -->
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## 预期行为
<!-- 请描述您期望的行为 -->

## 实际行为
<!-- 请描述实际发生的行为 -->

## 环境信息
<!-- 请提供您的环境信息 -->
- OS: [e.g. Windows 10]
- Python: [e.g. 3.10.0]
- Node.js: [e.g. 18.0.0]

## 日志
<!-- 如果有错误日志，请提供 -->
```

### 安全漏洞报告

**重要**: 如果您发现安全漏洞，请不要在公开 Issue 中报告。请发送邮件至项目维护者，我们会尽快处理。

---

## 功能建议

### 功能建议模板

```markdown
## 功能描述
<!-- 请清晰描述您建议的功能 -->

## 使用场景
<!-- 请描述这个功能的使用场景 -->

## 建议的解决方案
<!-- 如果您有具体的实现建议，请提供 -->

## 参考资料
<!-- 如果有相关的文档、链接或截图，请提供 -->
```

---

## 开发资源

### 相关文档

- [后端开发文档](./backend/README.md)
- [前端开发文档](./frontend/README.md)
- [API 接口文档](./api/README.md)
- [配置指南](./configuration.md)
- [部署指南](./deployment.md)

### 相关工具

- **IDE**: PyCharm, VS Code
- **API 测试**: Postman, Thunder Client
- **数据库工具**: DB Browser for SQLite
- **版本控制**: Git

---

## 许可证

通过贡献代码，您同意将您的作品按照项目的 MIT 许可证发布。

---

## 联系方式

- 提交 GitHub Issue
- 发送 Pull Request
- 参与讨论

感谢您的贡献！