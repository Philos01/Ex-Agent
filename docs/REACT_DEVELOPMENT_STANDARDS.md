# ReAct Agent 第一阶段代码开发与验证制度

## 📋 目录
1. [代码编写规范](#1-代码编写规范)
2. [代码审查流程](#2-代码审查流程)
3. [单元测试标准](#3-单元测试标准)
4. [集成测试要求](#4-集成测试要求)
5. [技术约束与安全标准](#5-技术约束与安全标准)
6. [实施计划](#6-实施计划)

---

## 1. 代码编写规范

### 1.1 Python 代码风格
- 严格遵循 [PEP 8](https://peps.python.org/pep-0008/) 标准
- 使用 4 空格缩进，禁止使用 Tab
- 最大行长度：120 字符
- 文件顶部必须包含文档字符串（docstring）

### 1.2 类型注解
- 所有函数参数和返回值必须使用类型注解
- 使用 `typing` 模块中的类型（List, Dict, Optional, Tuple 等）
- 示例：
  ```python
  from typing import List, Dict, Optional, Tuple
  
  def parse_action(text: str) -> Tuple[Optional[str], Optional[Dict]]:
      """解析 Action 和 Action Input"""
      pass
  ```

### 1.3 文档字符串
- 所有公共函数、类、方法必须包含 Google 风格的文档字符串
- 文档字符串应包含：功能描述、参数说明、返回值说明、异常说明
- 示例：
  ```python
  def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
      """
      执行指定的工具
      
      Args:
          tool_name: 工具名称
          params: 工具参数字典
          
      Returns:
          工具执行结果，包含 success 字段
          
      Raises:
          ToolNotFoundError: 当工具不存在时
          ToolExecutionError: 当工具执行失败时
      """
      pass
  ```

### 1.4 日志规范
- 使用 Python 标准 `logging` 模块
- 日志级别：
  - `DEBUG`: 详细调试信息
  - `INFO`: 一般信息（如初始化完成）
  - `WARNING`: 警告信息（如工具降级）
  - `ERROR`: 错误信息（如工具执行失败）
- 日志格式：`[模块名] 消息内容`
- 示例：
  ```python
  import logging
  logger = logging.getLogger(__name__)
  
  logger.info("[ReActAgent] Initializing...")
  logger.debug(f"[ReActAgent] Scratchpad: {scratchpad}")
  logger.error(f"[ReActAgent] Tool execution failed: {e}")
  ```

### 1.5 错误处理
- 使用自定义异常类，继承自 `Exception`
- 捕获异常时必须记录日志
- 不要使用裸 `except:`，必须指定异常类型
- 示例：
  ```python
  class ReActAgentError(Exception):
      """ReAct Agent 基础异常"""
      pass
  
  class OutputParseError(ReActAgentError):
      """输出解析错误"""
      pass
  
  class MaxIterationsReached(ReActAgentError):
      """达到最大迭代次数"""
      pass
  ```

### 1.6 安全编码规范
- **禁止**在日志中输出敏感信息（API Key、密码等）
- **禁止**将用户输入直接拼接到命令或查询中
- 使用参数化查询
- 对文件路径进行安全验证，防止路径遍历攻击

---

## 2. 代码审查流程

### 2.1 审查清单
代码提交前必须通过以下检查：
- [ ] 代码符合 PEP 8 规范
- [ ] 所有公共 API 有完整的文档字符串
- [ ] 类型注解完整
- [ ] 新增代码有对应的单元测试
- [ ] 所有现有测试通过
- [ ] 没有遗留的调试代码（print 语句、注释掉的代码等）
- [ ] 日志记录恰当
- [ ] 错误处理完善

### 2.2 自审步骤
1. 运行代码格式化工具：`black .`
2. 运行代码检查工具：`flake8`
3. 运行类型检查：`mypy`
4. 运行单元测试：`pytest tests/`
5. 检查测试覆盖率：`pytest --cov=app/agents`

---

## 3. 单元测试标准

### 3.1 测试框架
- 使用 `pytest` 作为测试框架
- 测试文件命名：`test_*.py`
- 测试函数命名：`test_*`

### 3.2 测试覆盖要求
- 核心模块测试覆盖率 ≥ 80%
- 关键路径测试覆盖率 100%

### 3.3 测试分类
- **单元测试**：测试单个函数/类，隔离外部依赖
- **集成测试**：测试多个组件协作
- **端到端测试**：测试完整流程

### 3.4 Mock 规范
- 使用 `unittest.mock` 或 `pytest-mock`
- Mock 外部 LLM 调用
- Mock 工具执行
- Mock 文件 I/O

### 3.5 测试示例
```python
import pytest
from app.agents.output_parser import OutputParser

def test_parse_json_success():
    """测试成功解析 JSON 输出"""
    parser = OutputParser()
    text = '''```json
    {
        "thought": "我需要搜索",
        "action": "search",
        "action_input": {"query": "test"},
        "is_final_answer": false
    }
    ```'''
    result = parser.parse(text)
    assert result["thought"] == "我需要搜索"
    assert result["action"] == "search"

def test_parse_invalid_json():
    """测试解析无效 JSON"""
    parser = OutputParser()
    with pytest.raises(OutputParseError):
        parser.parse("invalid json")
```

---

## 4. 集成测试要求

### 4.1 测试场景
- 完整 ReAct 循环测试（不调用真实 LLM）
- 工具调用集成测试
- 多步决策测试
- 错误恢复测试

### 4.2 测试环境
- 使用独立的测试配置
- Mock 外部 API 调用
- 使用临时目录进行文件操作

---

## 5. 技术约束与安全标准

### 5.1 LLM 调用规则
- 复用现有 `qa.py` 中的 LLM 调用逻辑
- 支持 OpenAI 和 Ollama 双提供商
- 遵守配置中的 `temperature`、`max_tokens` 等参数
- 实现超时控制（默认 60 秒）
- 实现重试机制（最多 3 次）

### 5.2 技能使用规范
- 复用现有的 `SkillManager` 系统
- 技能调用前验证技能存在
- 技能参数验证
- 错误处理：技能执行失败作为 Observation 返回给 LLM

### 5.3 技术约束
- **不引入**新的外部依赖（除非必要）
- 保持与现有代码库的风格一致
- 向后兼容：ReAct 模式通过配置开关控制
- 性能：单次 ReAct 循环 ≤ 5 步

### 5.4 安全标准
- 敏感信息（API Key）不记录在日志中
- 用户输入经过验证后再传递给工具
- 技能执行在沙箱环境中（使用现有的 SkillExecutor）
- 最大迭代次数限制（防止死循环）

---

## 6. 实施计划

### 第一阶段：基础 ReAct 循环（MVP）
**目标**：建立最小可行的 ReAct 循环

| 任务 | 优先级 | 预计时间 |
|------|--------|---------|
| 创建 agents/ 目录结构 | 高 | 5 分钟 |
| 实现 MemoryScratchpad | 高 | 30 分钟 |
| 实现 OutputParser | 高 | 45 分钟 |
| 实现 PromptEngine | 高 | 45 分钟 |
| 实现 ReActAgent 核心 | 高 | 60 分钟 |
| 编写单元测试 | 中 | 60 分钟 |
| 集成到 qa.py | 中 | 30 分钟 |
| 集成测试 | 中 | 30 分钟 |

### 里程碑
- [ ] 代码库结构建立
- [ ] 所有核心模块完成
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] 可通过配置开关启用/禁用

---

## 附录 A：配置文件示例

```json
{
  "react": {
    "enabled": false,
    "max_iterations": 5,
    "output_format": "json",
    "use_few_shot": true,
    "timeout": 60,
    "max_retries": 3
  }
}
```

---

## 附录 B：文件结构

```
backend/app/agents/
├── __init__.py              # 模块初始化
├── exceptions.py            # 自定义异常
├── memory.py                # MemoryScratchpad
├── output_parser.py         # OutputParser
├── prompt_engine.py         # PromptEngine
└── react_agent.py           # ReActAgent

backend/tests/agents/
├── __init__.py
├── test_memory.py
├── test_output_parser.py
├── test_prompt_engine.py
└── test_react_agent.py
```

---

**版本**: 1.0
**最后更新**: 2026-04-16
**维护者**: 开发团队
