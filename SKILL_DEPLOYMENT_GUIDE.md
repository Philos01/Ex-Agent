
# ClawHub 技能部署系统使用指南

## 概述

本系统实现了将 ClawHub 平台下载的技能包一键部署到 Agent 系统的功能。

## ClawHub 技能包格式

一个标准的 ClawHub 技能包包含以下文件：

```
skill-name-1.0.0/
├── SKILL.md          # 技能说明文档（必需）
├── _meta.json        # 技能元数据（可选）
└── scripts/          # 其他资源文件（可选）
    └── example.sh
```

### SKILL.md 格式

必需包含 YAML frontmatter：

```markdown
---
name: skill-name
description: 技能描述，说明技能功能和使用场景
---

# 技能标题

详细的技能说明...
```

### _meta.json 格式

```json
{
  "ownerId": "xxx",
  "slug": "skill-name",
  "version": "1.0.0",
  "publishedAt": 1234567890
}
```

## 使用方法

### 1. 从 ClawHub 下载技能包

首先，从 ClawHub 平台下载你需要的技能包，解压到本地目录。

### 2. 查看技能包信息

在部署前，你可以先查看技能包的详细信息：

```bash
cd backend
python skill_deployer.py info &lt;技能包路径&gt;
```

**示例：**

```bash
python skill_deployer.py info ../arxiv-watcher-1.0.0
```

这会显示：
- 技能包路径
- 技能名称
- SKILL.md frontmatter 内容
- _meta.json 内容
- 技能包目录结构

### 3. 部署技能包

使用 `deploy` 命令部署技能包：

```bash
python skill_deployer.py deploy &lt;技能包路径&gt;
```

**示例：**

```bash
python skill_deployer.py deploy ../arxiv-watcher-1.0.0
```

部署过程会自动完成以下步骤：

1. **验证技能包** - 检查 SKILL.md 是否存在，解析元数据
2. **复制技能包** - 将技能包复制到 `skills/` 目录
3. **生成实现** - 自动创建 Python 技能实现文件
4. **更新配置** - 更新 `skills_config.yaml`
5. **验证部署** - 确认所有文件都已正确部署

### 4. 自定义配置（可选）

你可以在部署时传入自定义配置：

```bash
python skill_deployer.py deploy &lt;技能包路径&gt; --config '{"enabled": true, "custom_option": "value"}'
```

**示例：**

```bash
python skill_deployer.py deploy ../arxiv-watcher-1.0.0 --config '{"enabled": true, "max_results": 10}'
```

### 5. 列出已安装的技能

查看当前系统中已安装的所有技能：

```bash
python skill_deployer.py list
```

这会显示：
- 已安装的技能列表
- 每个技能的启用/禁用状态
- 技能版本信息

### 6. 重启后端服务

部署完成后，需要重启后端服务以加载新技能：

```bash
# 如果后端服务正在运行，先停止它
# 然后重新启动
python -m uvicorn app.main:app --reload --port 8001
```

## 部署后的文件结构

部署成功后，系统会创建/更新以下文件：

```
项目根目录/
├── skills/
│   ├── weather_search/          # 已存在的技能
│   └── arxiv-watcher/           # 新部署的技能
│       ├── SKILL.md
│       ├── _meta.json
│       └── scripts/
│           └── search_arxiv.sh
├── skills_config.yaml            # 更新的配置文件
└── backend/
    └── app/
        └── skills/
            ├── weather_search.py
            └── arxiv-watcher.py  # 自动生成的实现文件
```

## 技能实现文件说明

系统会自动生成 Python 技能实现文件，例如 `arxiv-watcher.py`：

```python
@skill
class ArxivWatcherSkill(BaseSkill):
    name = "arxiv-watcher"
    description = "..."
    version = "1.0.0"
    
    @property
    def instructions(self):
        # 自动从 skills/arxiv-watcher/SKILL.md 读取
        ...
    
    def execute(self, **kwargs):
        # 基础实现，可根据需要自定义
        return {
            "success": True,
            "message": "arxiv-watcher skill executed",
            "data": kwargs
        }
```

你可以根据技能的具体需求，修改 `execute` 方法来实现实际功能。

## 常见问题

### Q: 部署失败怎么办？
A: 检查：
1. 技能包路径是否正确
2. 技能包是否包含 SKILL.md 文件
3. 是否有足够的权限写入文件

### Q: 如何更新已部署的技能？
A: 重新运行 deploy 命令即可，系统会自动备份旧版本

### Q: 如何删除已部署的技能？
A: 手动删除以下内容：
1. `skills/&lt;技能名&gt;/` 目录
2. `backend/app/skills/&lt;技能名&gt;.py` 文件
3. `skills_config.yaml` 中的对应配置

### Q: 技能部署后不生效？
A: 确保：
1. 已重启后端服务
2. 技能在 `skills_config.yaml` 中设置为 `enabled: true`

## 命令参考

```
usage: skill_deployer.py [-h] {deploy,info,list} ...

ClawHub 技能部署器 - 一键部署 ClawHub 技能包到 Agent 系统

命令:
  {deploy,info,list}
    deploy            部署技能包
    info              查看技能包信息
    list              列出已安装的技能

示例:
  # 部署本地技能包
  python skill_deployer.py deploy ../arxiv-watcher-1.0.0
  
  # 部署并自定义配置
  python skill_deployer.py deploy ../arxiv-watcher-1.0.0 --config '{"enabled": true}'
  
  # 查看技能包信息
  python skill_deployer.py info ../arxiv-watcher-1.0.0
  
  # 列出已安装的技能
  python skill_deployer.py list
```

