# API Key 安全检查清单

## ✅ 已完成的安全措施

1. ✅ **.gitignore 正确配置**
   - `.env` 已被忽略
   - `config.json` 已被忽略
   - 数据库文件已被忽略

2. ✅ **代码中无硬编码 Key**
   - 所有 API Key 通过环境变量读取
   - 没有 `sk-` 或其他 Key 硬编码在代码中

3. ✅ **配置文件安全保存**
   - `config.json.example` 只包含示例配置
   - 实际配置在本地 `.env` 和 `config.json` 中（被忽略）

## 🔒 后续提交安全操作指南

### 1. 提交前必检查

每次 `git add` 和 `git commit` 前，先运行：

```bash
git diff --cached
```

检查是否有以下内容被加入提交：
- ❌ `.env` 文件
- ❌ `config.json` 文件
- ❌ 任何包含 `api_key` 或 `sk-` 的文件

### 2. 使用安全提交检查

创建一个 git pre-commit hook 来自动检查：

在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/sh
# 检查是否有敏感文件被提交
if git diff --cached --name-only | grep -E "\.(env|config\.json)$"; then
    echo "❌ 错误：不允许提交敏感文件！"
    echo "检查 .gitignore 是否正确配置"
    exit 1
fi

# 检查代码中是否有硬编码的 Key
if git diff --cached | grep -E "sk-|api_key"; then
    echo "❌ 错误：代码中发现疑似 API Key！"
    echo "请移除后再提交"
    exit 1
fi

echo "✅ 安全检查通过"
exit 0
```

然后运行：
```bash
chmod +x .git/hooks/pre-commit
```

### 3. 配置文件使用流程

#### 创建 .env 文件
在项目根目录创建 `.env`：
```env
# OpenAI / DeepSeek
OPENAI_API_KEY=你的新Key
OPENAI_BASE_URL=https://api.openai.com/v1
DEEPSEEK_API_KEY=你的DeepSeekKey

# 高德天气
AMAP_API_KEY=你的高德Key

# 数据库
DATABASE_URL=sqlite:///data/lab_agent.db
SECRET_KEY=你的随机Secret
```

#### 创建 config.json
在项目根目录创建 `config.json`（使用 `config.json.example` 作为模板）：

```bash
cp config.json.example config.json
```

然后修改 `config.json` 中的配置项（**不要在这里添加 API Key！**）

## 📝 安全最佳实践

### ✅ 应该做的

1. **定期检查 git diff**
   ```bash
   git status
   git diff
   ```

2. **使用 .gitignore 保护敏感文件**
   - 确认 `.env` 和 `config.json` 在 `.gitignore` 中
   - 添加其他敏感配置到 `.gitignore`

3. **使用环境变量**
   - 所有 API Key 都用环境变量
   - 不要在代码中硬编码

4. **使用配置示例**
   - `config.json.example` 只包含示例值
   - 实际配置在本地文件中（被忽略）

### ❌ 不要做的

1. ❌ **不要提交 `.env` 或 `config.json`**
2. ❌ **不要在代码中硬编码 `sk-` 或其他 Key**
3. ❌ **不要在 GitHub Issues / PR 中粘贴 Key**
4. ❌ **不要在文档中包含真实 Key**

## 🔍 快速安全检查命令

每次提交前运行：

```bash
# 检查即将提交的内容
git diff --cached

# 检查是否有敏感文件
git status --ignored

# 检查 git 历史（如果怀疑有泄漏）
git log --stat
```

## ⚠️ 万一再次发生泄漏怎么办？

1. **立即撤销泄漏的 Key** - 这是最重要的
2. **检查 git 历史** - 使用 `git log --oneline --grep="api\|key"`
3. **清理 git 历史**（如果需要）
4. **重新生成新的 Key**

## 📌 当前状态确认

当前项目的安全状态：
- ✅ `.gitignore` 配置正确
- ✅ 代码中无硬编码 Key
- ✅ 正在使用新的 API Key
- ⚠️ Git 历史中有旧的 Key（但您说 Key 已改）

**只要您不把新的 Key 提交到 git 中，就是安全的！**
