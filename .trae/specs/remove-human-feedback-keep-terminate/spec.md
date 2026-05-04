# 移除人类反馈机制、保留终止按钮 Spec

## Why
当前系统中的人类反馈机制（HumanFeedbackService、FeedbackRequest、FEEDBACK_REQUEST 事件等）会在 AgentLoop 的每次思考后阻塞等待用户反馈，导致流程繁琐、响应慢、且不符合"AI 自主执行 + 用户一键终止"的工业需求。需要简化交互，移除复杂的反馈等待逻辑，仅保留一个"终止按钮"让用户可以在 Agent 运行时停止执行。

## What Changes
- **移除** `HumanFeedbackService` 的 wait_for_feedback 阻塞逻辑
- **移除** `AgentLoop` 中的 FEEDBACK_REQUEST 发送和 wait_for_feedback 等待逻辑
- **移除** 前端 HumanFeedbackInput 组件的反馈表单部分（保留终止按钮）
- **移除** 反馈类型：tool_call_suggestion、parameter_adjustment、strategy_modification、general_comment
- **保留** termination 相关逻辑（终止按钮 → execution_termination → Agent 停止）
- **保留** 反馈历史查看页面（仅显示终止事件记录）
- **BREAKING**: feedback API 端点行为简化，仅支持终止提交

## Impact
- Affected specs: 人类反馈机制（完全移除等待逻辑）
- Affected code:
  - `backend/app/agents/agent_loop.py` — 移除 FEEDBACK_REQUEST/等待逻辑
  - `backend/app/services/human_feedback_service.py` — 简化，保留基础存储
  - `backend/app/agents/types.py` — 精简 FeedbackType
  - `backend/app/services/qa/react_stream.py` — 简化反馈事件透传
  - `backend/app/api/routes.py` — 简化反馈 API
  - `frontend/src/components/gen-ui/HumanFeedbackInput.vue` — 移除表单，保留终止按钮
  - `frontend/src/components/gen-ui/FeedbackHistory.vue` — 简化展示
  - `frontend/src/views/ChatView.vue` — 简化反馈交互
  - `frontend/src/components/gen-ui/ReActThinkingDisplay.vue` — 移除步骤旁反馈按钮，仅保留全局终止

## ADDED Requirements

### Requirement: 全局终止按钮
系统 SHALL 在前端 ChatView 中提供一个可见的"终止执行"按钮，在 Agent 运行期间显示，点击后向后端发送终止请求。

#### Scenario: 终止 Agent 执行
- **WHEN** Agent 正在执行（SSE 连接活跃）
- **AND** 用户点击"终止执行"按钮
- **THEN** 系统向后端发送终止请求
- **AND** Agent 停止执行并返回当前已获得的结果

## MODIFIED Requirements

### Requirement: FeedbackType 枚举
原要求：支持 5 种反馈类型（tool_call_suggestion / parameter_adjustment / execution_termination / strategy_modification / general_comment）。
修改为：仅保留 `EXECUTION_TERMINATION` 和 `CONTINUE_EXECUTION` 两种类型。

### Requirement: AgentLoop 反馈集成
原要求：在每次思考后发送 FEEDBACK_REQUEST 并等待用户反馈（最多 10 分钟超时）。
修改为：**移除** FEEDBACK_REQUEST 发送和 wait_for_feedback 等待逻辑。AgentLoop 继续正常执行，仅在检测到 `execution_termination` 反馈时停止（由前端主动触发）。

### Requirement: HumanFeedbackInput 组件
原要求：提供完整的反馈输入界面（类型选择、参数编辑、工具替换等）。
修改为：**仅保留**终止按钮，移除所有反馈表单输入控件。

### Requirement: ReActThinkingDisplay 步骤反馈
原要求：在每个 action 步骤旁添加反馈按钮，展开反馈面板。
修改为：**移除**步骤级反馈按钮，改为在 ChatView 顶部提供全局终止按钮。

## REMOVED Requirements

### Requirement: 思考后等待反馈
**Reason**: 阻塞式等待严重影响用户体验和响应速度，不符合"AI 自主执行 + 用户一键终止"的工业需求。
**Migration**: 移除 wait_for_feedback 调用，AgentLoop 自主执行不被反馈阻塞。

### Requirement: 工具调用建议/参数调整/策略修改反馈
**Reason**: 这些复杂交互不再支持，简化为仅保留终止功能。
**Migration**: 前端移除对应输入控件，后端移除对应处理逻辑。

### Requirement: 反馈历史详细展示
**Reason**: 反馈类型大幅简化，无需展示复杂的反馈参数。
**Migration**: 保留终止事件记录展示，移除其他反馈类型的详细展示。
