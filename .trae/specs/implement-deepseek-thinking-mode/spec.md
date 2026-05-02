# DeepSeek 思考模式完整实现 Spec

## Why
当前前端的思考模式开关虽然存在，但并未真正影响 DeepSeek API 的思考模式参数传递。根据 DeepSeek 官方文档要求，需要正确实现思考模式开关、工具调用时的 `reasoning_content` 回传、多轮对话拼接逻辑，以及提供思考强度（reasoning effort）调节功能，以提升模型推理质量和用户体验。

## What Changes
- **前端改进**:
  - 修改 Thinking 按钮行为，确保正确传递思考模式参数到后端
  - 新增思考强度调节按钮（类似图片中的 toggle 样式），点击弹出选项面板
  - 支持选择：low/medium/high/max 四个级别
  - 在参数侧边栏中显示当前思考模式和强度设置
  
- **后端改进**:
  - 修改 `LLMClient` 和 API 路由，支持接收并处理 `thinking` 参数（通过 `extra_body` 传递）
  - 支持 `reasoning_effort` 参数传递给 DeepSeek API
  - 实现正确的多轮对话拼接逻辑：
    - 非工具调用轮次：`reasoning_content` 不参与上下文拼接
    - 工具调用轮次：必须回传 `reasoning_content`
  - 确保流式响应正确返回 `reasoning_content`

- **数据结构变更**:
  - QARequest 新增字段：`reasoning_effort: Optional[str]`
  - LLMConfig 新增字段：`reasoning_effort: str = "high"`
  - 前端 params 新增：`reasoning_effort`

## Impact
- Affected specs: DeepSeek API 集成、多轮对话管理、工具调用流程
- Affected code:
  - Frontend: [ChatView.vue](frontend/src/views/ChatView.vue), [appStore.js](frontend/src/stores/appStore.js)
  - Backend: [llm_client.py](backend/app/agents/llm_client.py), [routes.py](backend/app/api/routes.py), [qa.py](backend/app/services/qa.md)

## ADDED Requirements

### Requirement: 思考模式开关与参数传递
系统 SHALL 提供正确的思考模式开关功能，确保前端设置能够正确传递到 DeepSeek API。

#### Scenario: 启用思考模式
- **WHEN** 用户点击 Thinking 按钮启用思考模式
- **THEN** 前端发送 `enable_thinking=true` 和 `reasoning_effort` 到后端
- **AND** 后端在调用 DeepSeek API 时，通过 `extra_body={"thinking": {"type": "enabled"}}` 启用思考模式
- **AND** 同时传递 `reasoning_effort` 参数控制思考强度

#### Scenario: 禁用思考模式
- **WHEN** 用户点击 Thinking 按钮禁用思考模式
- **THEN** 前端发送 `enable_thinking=false` 到后端
- **AND** 后端不传递 thinking 相关参数或传递 `{"thinking": {"type": "disabled"}}`

### Requirement: 思考强度调节 UI
系统 SHALL 提供类似图片效果的思考强度调节按钮，支持用户选择不同的思考强度等级。

#### Scenario: 显示思考强度选项
- **WHEN** 用户点击思考强度调节按钮（显示为 "工作量 (High)" 样式的 toggle）
- **THEN** 弹出选项面板，显示以下选项：
  - Low - 快速响应，适合简单问题
  - Medium - 平衡模式
  - High (默认) - 深度思考，适合复杂问题
  - Max - 最大思考强度，消耗更多计算资源
- **AND** 用户选择后，按钮文字更新为 "工作量 (选择的等级)"
- **AND** 选中的选项高亮显示

#### Scenario: 传递思考强度参数
- **WHEN** 用户选择了思考强度等级
- **THEN** 该参数随请求一起发送到后端
- **AND** 后端将其映射为 DeepSeek API 的 `reasoning_effort` 参数值（注意：low/medium 会映射为 high）

### Requirement: 多轮对话拼接规则
系统 SHALL 按照 DeepSeek 文档要求实现正确的多轮对话拼接逻辑。

#### Scenario: 非工具调用的对话轮次
- **WHEN** 模型在某轮未进行工具调用
- **THEN** 下一轮请求时，该轮的 `reasoning_content` 不拼接到 messages 中（API 会忽略）
- **AND** 只保留 `role`, `content` 字段

#### Scenario: 工具调用的对话轮次
- **WHEN** 模型在某轮进行了工具调用
- **THEN** 下一轮及后续所有请求必须完整回传 `reasoning_content`
- **AND** messages 中包含完整的 assistant 消息：`role`, `content`, `reasoning_content`, `tool_calls`
- **AND** 如果未正确回传，API 返回 400 错误

### Requirement: 流式响应处理
系统 SHALL 正确处理思考模式下的流式响应，包括 `reasoning_content` 的实时展示。

#### Scenario: 接收思考内容流
- **WHEN** 后端从 DeepSeek API 接收到 `reasoning_content` delta
- **THEN** 通过 SSE 发送 `reasoning_chunk` 事件到前端
- **AND** 前端实时更新 DeepSeekThinkingPreview 组件显示思考内容

## MODIFIED Requirements

### Requirement: QARequest 数据模型
修改现有的 QARequest 模型，新增思考相关字段：

```python
class QARequest(BaseModel):
    # ... existing fields ...
    enable_thinking: bool = None  # 是否启用思考阶段
    reasoning_effort: str = None  # 思考强度: low/medium/high/max
    use_react: bool = None  # 是否启用 ReAct 多步推理模式
```

### Requirement: LLMConfig 配置
修改 LLMConfig，新增 reasoning_effort 字段：

```python
@dataclass
class LLMConfig:
    # ... existing fields ...
    enable_thinking: bool = False
    reasoning_effort: str = "high"  # 默认高强度思考
```

### Requirement: LLMClient._openai_chat_kwargs 方法
修改该方法以支持思考模式参数：

```python
def _openai_chat_kwargs(self, messages: List[Dict], **extra) -> Dict[str, Any]:
    kwargs = dict(
        model=model,
        messages=messages,
        max_tokens=self.config.max_tokens,
        **extra,
    )
    
    if self.provider == "deepseek" and self.config.enable_thinking:
        kwargs["reasoning_effort"] = self.config.reasoning_effort
        kwargs["extra_body"] = {
            "thinking": {"type": "enabled"}
        }
    
    # deepseek-reasoner does not support temperature/top_p in thinking mode
    if not (self.provider == "deepseek" and self.config.enable_thinking):
        kwargs["temperature"] = self.config.temperature
        kwargs["top_p"] = self.config.top_p
    
    return kwargs
```

## REMOVED Requirements
无

## Technical Notes

### DeepSeek API 兼容性注意事项
1. 思考模式下不支持 `temperature`, `top_p`, `presence_penalty`, `frequency_penalty` 参数
2. `reasoning_effort` 的 `low` 和 `medium` 值会映射为 `high`，`xhigh` 会映射为 `max`
3. 必须使用 OpenAI SDK 的 `extra_body` 参数传递 `thinking` 配置

### UI 设计参考
参考提供的图片样式，实现类似 Claude Code 的模式选择器：
- Toggle 按钮显示当前选中状态
- 点击后弹出浮层选项列表
- 支持键盘导航和 ESC 关闭
- 选项包含图标、标题、描述文字
