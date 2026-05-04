# Tasks

## 后端部分

- [x] Task 1: 精简 `backend/app/agents/types.py` 中的 FeedbackType 枚举
  - [x] SubTask 1.1: 仅保留 EXECUTION_TERMINATION 和 CONTINUE_EXECUTION 两种类型
  - [x] SubTask 1.2: 移除不需要的 FeedbackRequest 字段（tool_name, tool_parameters）

- [x] Task 2: 修改 `backend/app/agents/agent_loop.py`，移除 FEEDBACK_REQUEST 和 wait_for_feedback 阻塞逻辑
  - [x] SubTask 2.1: 移除每次思考后发送 FEEDBACK_REQUEST 事件
  - [x] SubTask 2.2: 移除 wait_for_feedback 调用和 10 分钟超时等待
  - [x] SubTask 2.3: 简化 _check_feedback 方法，仅保留终止检测
  - [x] SubTask 2.4: 移除 _apply_feedback 中的 tool_call_suggestion/parameter_adjustment/strategy_modification 处理

- [x] Task 3: 简化 `backend/app/services/human_feedback_service.py`
  - [x] SubTask 3.1: 保留基础提交/查询功能
  - [x] SubTask 3.2: 移除 wait_for_feedback 阻塞方法

- [x] Task 4: 简化 `backend/app/api/routes.py` 反馈 API
  - [x] SubTask 4.1: POST /api/feedback 仅支持终止提交

## 前端部分

- [x] Task 5: 修改 `frontend/src/components/gen-ui/HumanFeedbackInput.vue`
  - [x] SubTask 5.1: 移除反馈类型选择器
  - [x] SubTask 5.2: 移除文本输入框、工具选择器、参数编辑器
  - [x] SubTask 5.3: 仅保留"终止执行"按钮

- [x] Task 6: 修改 `frontend/src/components/gen-ui/ReActThinkingDisplay.vue`
  - [x] SubTask 6.1: 移除每个 action 步骤旁的反馈按钮
  - [x] SubTask 6.2: 移除步骤级反馈面板

- [x] Task 7: 修改 `frontend/src/views/ChatView.vue`
  - [x] SubTask 7.1: 添加全局"终止执行"按钮（Agent 运行期间可见）
  - [x] SubTask 7.2: 移除步骤级反馈交互

- [x] Task 8: 简化 `frontend/src/components/gen-ui/FeedbackHistory.vue`
  - [x] SubTask 8.1: 仅显示终止事件记录
  - [x] SubTask 8.2: 移除复杂参数展示

## 清理与测试

- [x] Task 9: 清理不需要的反馈事件类型处理
  - [x] SubTask 9.1: `backend/app/services/qa/react_stream.py` 移除不需要的反馈事件透传
  - [x] SubTask 9.2: `frontend/src/constants/sseEvents.js` 移除不需要的反馈事件常量

- [x] Task 10: 验证功能
  - [x] SubTask 10.1: 验证 Agent 正常执行不被阻塞
  - [x] SubTask 10.2: 验证终止按钮可正常停止 Agent
  - [x] SubTask 10.3: 验证反馈历史页面正确显示终止记录

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 1
- Task 4 依赖 Task 2
- Task 5 独立
- Task 6 独立
- Task 7 依赖 Task 5
- Task 8 依赖 Task 5
- Task 9 依赖 Task 2 和 Task 5
- Task 10 依赖所有其他任务
