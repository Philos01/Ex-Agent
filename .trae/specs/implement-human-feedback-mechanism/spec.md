# 人类反馈机制 Spec

## Why
当前Agent系统在ReAct模式下以5次迭代硬限制运行，用户无法在执行过程中干预Agent的行为（如调整工具参数、终止执行、修改策略）。引入人类反馈机制可以让用户实时指导Agent的决策过程，提高系统的可控性和实用性，同时移除迭代限制使Agent能够持续执行直到任务完成或用户主动终止。

## What Changes
- 新增人类反馈数据模型和反馈服务，支持反馈的存储、查询和统计
- 在Agent执行循环中集成反馈检查点，支持5种反馈类型的处理
- 移除ReAct模式的5次迭代硬限制，改为无限迭代（通过人类反馈或AI自判断终止）
- 新增反馈提交/查询API端点
- 扩展SSE事件类型，支持反馈请求和反馈确认通知
- 前端新增反馈输入组件，在ReAct执行步骤中嵌入反馈交互
- 前端新增反馈历史查看页面

## Impact
- Affected specs: ReAct Agent执行引擎、QA流式响应、前端聊天界面
- Affected code:
  - `backend/app/agents/types.py` — 新增反馈相关类型定义
  - `backend/app/agents/agent_loop.py` — 集成反馈检查点、移除迭代限制
  - `backend/app/services/qa/react_stream.py` — 透传反馈相关SSE事件
  - `backend/app/api/routes.py` — 新增反馈API端点
  - `backend/app/models/__init__.py` — 注册新模型
  - `frontend/src/views/ChatView.vue` — 集成反馈交互
  - `frontend/src/components/gen-ui/ReActThinkingDisplay.vue` — 步骤级反馈按钮
  - `frontend/src/router/index.js` — 新增反馈历史路由

## ADDED Requirements

### Requirement: 反馈数据模型
系统 SHALL 提供人类反馈的数据模型，包含以下字段：
- id: 自增主键
- session_id: 关联的会话ID
- iteration: Agent执行迭代轮次
- feedback_type: 反馈类型枚举（tool_call_suggestion / parameter_adjustment / execution_termination / strategy_modification / general_comment）
- content: 反馈文本内容
- tool_name: 关联的工具名（可选）
- tool_parameters: 关联的工具参数JSON（可选）
- is_applied: 是否已被Agent应用
- created_at: 创建时间

#### Scenario: 创建反馈记录
- **WHEN** 用户提交一条反馈
- **THEN** 系统创建反馈记录并加入会话的反馈队列，返回反馈ID

### Requirement: 反馈服务
系统 SHALL 提供反馈服务（HumanFeedbackService），支持：
- 按会话ID存储和检索反馈
- 维护每个会话的反馈队列（内存中，按时间排序）
- 提供未处理反馈的取出操作
- 标记反馈为已应用
- 提供反馈统计（按类型、按会话）

#### Scenario: 存储和检索反馈
- **WHEN** 用户通过API提交反馈
- **THEN** 反馈被存储到SQLite数据库并加入内存队列
- **AND** Agent在检查点可以取出该反馈

#### Scenario: 反馈统计
- **WHEN** 请求反馈统计
- **THEN** 返回按类型分组的反馈数量和已应用率

### Requirement: Agent类型扩展
系统 SHALL 在 `backend/app/agents/types.py` 中新增：
- `FeedbackType` 枚举：5种反馈类型
- `FeedbackRequest` 数据类：封装反馈请求
- `FeedbackResponse` 数据类：封装反馈处理结果
- `FeedbackState` 枚举：pending / accepted / rejected
- `EventType` 新增 `FEEDBACK_REQUEST` 和 `FEEDBACK_ACCEPTED` 事件类型

#### Scenario: 类型定义完整性
- **WHEN** Agent需要处理反馈
- **THEN** 可以使用标准化的类型进行反馈的创建、传递和处理

### Requirement: AgentLoop反馈集成
系统 SHALL 在AgentLoop执行循环中集成反馈机制：
- 在每次思考（thought）后、每次行动（action）前设置反馈检查点
- 检查点从反馈队列取出未处理的反馈并执行
- 支持5种反馈类型的处理逻辑
- 移除5次迭代的硬限制，改为无限迭代
- 终止条件：AI自判断完成 / 用户通过反馈终止 / 用户通过前端停止按钮终止

#### Scenario: 工具调用建议反馈
- **WHEN** 用户提交tool_call_suggestion类型反馈
- **THEN** Agent用用户指定的工具和参数覆盖原始决策

#### Scenario: 参数调整反馈
- **WHEN** 用户提交parameter_adjustment类型反馈
- **THEN** Agent用调整后的参数执行当前工具调用

#### Scenario: 执行终止反馈
- **WHEN** 用户提交execution_termination类型反馈
- **THEN** Agent立即停止执行，返回当前已获得的部分结果

#### Scenario: 策略修改反馈
- **WHEN** 用户提交strategy_modification类型反馈
- **THEN** Agent根据用户指示调整执行策略（如修改检索方式、改变推理方向）

#### Scenario: 无限迭代
- **WHEN** Agent在ReAct模式下执行
- **THEN** 不受5次迭代限制，持续执行直到任务完成或收到终止信号
- **AND** 在每次迭代中检查反馈队列

### Requirement: 反馈API端点
系统 SHALL 提供以下API端点：
- `POST /api/feedback` — 提交反馈，请求体包含 session_id、feedback_type、content、tool_name（可选）、tool_parameters（可选）
- `GET /api/feedback/{session_id}` — 获取指定会话的反馈历史
- `GET /api/feedback/statistics` — 获取反馈统计信息

#### Scenario: 提交反馈
- **WHEN** 前端POST /api/feedback
- **THEN** 反馈被存储并加入会话队列，返回201和反馈ID

#### Scenario: 查询反馈历史
- **WHEN** 前端GET /api/feedback/{session_id}
- **THEN** 返回该会话的所有反馈记录，按时间排序

### Requirement: SSE反馈事件扩展
系统 SHALL 在SSE流中新增以下事件类型：
- `feedback_request`：Agent在检查点发出，通知前端可以提供反馈（包含当前迭代信息）
- `feedback_accepted`：Agent处理反馈后发出，通知前端反馈已被应用（包含反馈ID和处理结果）

#### Scenario: 反馈请求通知
- **WHEN** Agent到达反馈检查点
- **THEN** 通过SSE发送feedback_request事件，包含当前迭代号和可用工具列表

#### Scenario: 反馈确认通知
- **WHEN** Agent成功处理一条反馈
- **THEN** 通过SSE发送feedback_accepted事件，包含反馈ID和应用结果

### Requirement: 前端反馈输入组件
系统 SHALL 提供HumanFeedbackInput组件，支持：
- 选择反馈类型（5种）
- 输入反馈文本
- 对tool_call_suggestion类型提供工具选择和参数输入
- 对parameter_adjustment类型提供参数编辑界面
- 对execution_termination类型提供一键终止按钮
- 提交反馈到后端API

#### Scenario: 提交工具调用建议
- **WHEN** 用户在反馈输入中选择tool_call_suggestion类型并填写工具名和参数
- **THEN** 反馈被提交到后端，Agent在下一个检查点应用该反馈

#### Scenario: 终止执行
- **WHEN** 用户点击终止按钮
- **THEN** 提交execution_termination类型反馈，Agent停止执行

### Requirement: ReActThinkingDisplay反馈集成
系统 SHALL 在ReActThinkingDisplay组件的每个action步骤旁添加反馈按钮：
- 点击按钮展开反馈输入面板
- 面板预填当前步骤的工具名和参数
- 支持快速操作：调整参数、更换工具、终止执行

#### Scenario: 步骤级反馈
- **WHEN** 用户点击action步骤旁的反馈按钮
- **THEN** 展开反馈面板，预填当前工具信息，用户可修改后提交

### Requirement: 反馈历史页面
系统 SHALL 提供反馈历史查看页面（/feedback-history路由），展示：
- 按会话分组的反馈列表
- 每条反馈的类型、内容、是否已应用
- 反馈统计摘要

#### Scenario: 查看反馈历史
- **WHEN** 用户导航到/feedback-history
- **THEN** 显示所有会话的反馈历史，按时间倒序排列

## MODIFIED Requirements

### Requirement: ReAct迭代限制
原要求：Agent在ReAct模式下最多执行5次迭代。
修改为：Agent在ReAct模式下无迭代次数限制，持续执行直到任务完成或收到终止信号（人类反馈终止或AI自判断完成）。

### Requirement: SSE事件类型
原要求：SSE流支持 react_thought、react_action、react_observation、react_final_answer 等事件。
修改为：SSE流在原有事件基础上新增 feedback_request 和 feedback_accepted 事件类型。

## REMOVED Requirements

### Requirement: 最大迭代次数硬限制
**Reason**: 移除5次迭代限制，改为无限迭代+人类反馈控制终止。
**Migration**: max_iterations参数保留但默认值改为0（表示无限制），向后兼容。
