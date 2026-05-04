# Checklist

- [x] 后端 types.py 中 FeedbackType 仅保留 EXECUTION_TERMINATION 和 CONTINUE_EXECUTION 两种类型
- [x] 后端 agent_loop.py 中已移除 FEEDBACK_REQUEST 事件发送
- [x] 后端 agent_loop.py 中已移除 wait_for_feedback 阻塞调用
- [x] 后端 agent_loop.py 中 _apply_feedback 仅保留终止/继续处理逻辑
- [x] 后端 human_feedback_service.py 中已移除 wait_for_feedback 方法
- [x] 后端 routes.py 中 feedback API 已简化
- [x] 前端 HumanFeedbackInput.vue 已移除反馈表单，仅保留终止按钮
- [x] 前端 ReActThinkingDisplay.vue 已移除步骤级反馈按钮
- [x] 前端 ChatView.vue 有全局"终止执行"按钮且 Agent 运行期间可见
- [x] 前端 FeedbackHistory.vue 已简化，仅显示终止事件记录
- [x] 前端 sseEvents.js 中已移除不需要的反馈事件常量（该文件无反馈事件常量，无需修改）
- [x] 后端 react_stream.py 中已移除不需要的反馈事件透传
- [x] 验证：Agent 正常执行不被阻塞（无等待反馈逻辑）
- [x] 验证：终止按钮可正常停止 Agent 执行
- [x] 验证：反馈历史页面正确显示终止记录
