
# 技能系统重构设计文档

## 概述

本文档描述了项目中技能系统的重构方案，实现基于 YAML frontmatter 的技能选择和执行系统。

---

## 1. 架构设计

### 1.1 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| Metadata Parser | `metadata_parser.py` | 解析技能包 SKILL.md 的 YAML frontmatter |
| Skill Selector | `skill_selector.py` | 基于关键词或 LLM 选择技能 |
| Skill Executor | `skill_executor.py` | 执行 .sh 或 .py 技能文件 |
| New Skill Manager | `new_skill_manager.py` | 整合所有组件，提供统一接口 |

### 1.2 文件结构

```
backend/app/skills/
├── metadata_parser.py      # YAML frontmatter 解析器
├── skill_selector.py        # 技能选择器
├── skill_executor.py        # 技能执行器
├── new_skill_manager.py     # 新技能管理器
├── base.py                 # 旧系统基类（保留兼容）
├── discovery.py            # 旧系统发现器（保留兼容）
├── skill_manager.py        # 旧系统管理器（保留兼容）
└── ...
```

---

## 2. 功能说明

### 2.1 YAML Frontmatter 解析

**文件：** `metadata_parser.py`

**功能：**
- 解析 `SKILL.md` 文件开头的 YAML frontmatter
- 提取 `name` 和 `description` 字段
- 无需读取完整 SKILL.md 内容

**SKILL.md 格式示例：**
```markdown
---
name: arxiv-watcher
description: Search and summarize papers from ArXiv. Use when the user asks for the latest research, specific topics on ArXiv, or a daily summary of AI papers.
---

# ArXiv Watcher

完整的技能说明文档...
```

### 2.2 技能选择

**文件：** `skill_selector.py`

**功能：**
- 自动扫描 `skills/` 目录下的所有技能包
- 加载每个技能包的 YAML frontmatter
- 提供基于关键词的技能选择（回退方案）
- 预留 LLM 驱动的技能选择接口

### 2.3 技能执行

**文件：** `skill_executor.py`

**功能：**
- 自动查找技能包中的可执行文件（.sh 或 .py）
- 支持两种执行模式：
  1. Python 脚本封装调用
  2. Shell 脚本直接执行
- 参数注入机制：
  - Python: 通过临时 JSON 文件传递
  - Shell: 通过环境变量和命令行参数传递

**技能包结构示例：**
```
skills/arxiv-watcher/
├── SKILL.md              # 技能说明（含 YAML frontmatter）
├── _meta.json            # ClawHub 元数据
└── scripts/
    └── search_arxiv.sh   # 可执行脚本
```

### 2.4 新技能管理器

**文件：** `new_skill_manager.py`

**功能：**
- 整合所有新组件
- 提供与旧系统兼容的接口
- 优先使用新系统，回退到旧系统
- 合并新旧系统的技能列表

---

## 3. 使用指南

### 3.1 快速开始

```python
from app.skills.new_skill_manager import get_new_skill_manager

# 获取管理器
manager = get_new_skill_manager()

# 列出所有技能
skills = manager.list_skills()
print(skills)

# 判断是否使用技能
question = "有没有关于spectral super-resolution的最新研究"
use_skill, skill_name, params = manager.should_use_skill(question)

# 执行技能
if use_skill:
    result = manager.execute_skill(skill_name, **params)
    formatted = manager.format_skill_result(result)
    print(formatted)
```

### 3.2 部署新技能

1. 从 ClawHub 下载技能包到 `skills/` 目录
2. 确保技能包包含：
   - `SKILL.md`（含 YAML frontmatter）
   - 可执行文件（.sh 或 .py，在 scripts/ 或根目录）
3. 重启后端服务，新技能会自动加载

---

## 4. 向后兼容性

### 4.1 保留的旧系统

以下文件和功能完全保留，确保现有代码继续工作：
- `base.py` - BaseSkill 基类
- `discovery.py` - 技能发现器
- `skill_manager.py` - 旧技能管理器
- `arxiv-watcher.py` - Python 技能实现

### 4.2 迁移路径

1. 新代码使用 `get_new_skill_manager()`
2. 旧代码继续使用 `get_skill_manager()`
3. 两种管理器可以共存

---

## 5. 测试

### 5.1 单元测试

运行测试脚本：
```bash
cd backend
python test_new_skill_system.py
```

测试内容：
1. YAML frontmatter 解析
2. 技能选择器功能
3. 新技能管理器功能

---

## 6. 下一步

### 6.1 待实现功能

1. **LLM 驱动的技能选择** - 完全实现基于 LLM 的技能决策
2. **Skill 结果解析** - 更好地处理 .sh 脚本的 XML 输出
3. **性能优化** - 缓存技能元数据，减少重复解析

### 6.2 arxiv-watcher 集成

需要实现：
1. Python 脚本解析 `search_arxiv.sh` 的 XML 输出
2. 或重写 `search_arxiv.sh` 为 Python 脚本
3. 确保与现有 arxiv-watcher.py 的兼容性

---

## 总结

本重构方案：
- ✅ 实现了基于 YAML frontmatter 的技能发现
- ✅ 支持 .sh 和 .py 技能文件执行
- ✅ 完全向后兼容旧系统
- ✅ 提供清晰的迁移路径
- ✅ 为未来 LLM 驱动的技能选择预留接口

