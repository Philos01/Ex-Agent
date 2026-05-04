# Tasks

- [x] Task 1: 创建反馈数据模型和数据库表
  - [x] SubTask 1.1: 创建 `backend/app/models/human_feedback.py`，定义 HumanFeedback SQLAlchemy 模型
  - [x] SubTask 1.2: 在 `backend/app/models/__init__.py` 中注册新模型
  - [x] SubTask 1.3: 创建数据库迁移脚本，添加 human_feedback 表（由HumanFeedbackService自动创建）

- [x] Task 2: 扩展Agent类型定义
  - [x] SubTask 2.1: 在 `backend/app/agents/types.py` 中添加 FeedbackType 枚举（5种类型）
  - [x] SubTask 2.2: 添加 FeedbackRequest、FeedbackResponse 数据类
  - [x] SubTask 2.3: 添加 FeedbackState 枚举（pending/accepted/rejected）
  - [x] SubTask 2.4: 在 EventType 中新增 FEEDBACK_REQUEST 和 FEEDBACK_ACCEPTED

- [x] Task 3: 实现反馈服务
  - [x] SubTask 3.1: 创建 `backend/app/services/human_feedback_service.py`
  - [x] SubTask 3.2: 实现反馈存储（SQLite持久化 + 内存队列）
  - [x] SubTask 3.3: 实现按会话ID的反馈队列管理（入队、出队、标记已应用）
  - [x] SubTask 3.4: 实现反馈查询和统计功能
  - [x] SubTask 3.5: 实现单例模式获取服务实例

- [x] Task 4: 修改AgentLoop集成反馈机制并移除迭代限制
  - [x] SubTask 4.1: 修改 `backend/app/agents/agent_loop.py`，将 max_iterations 默认值改为0（无限制）
  - [x] SubTask 4.2: 修改执行循环，当 max_iterations=0 时使用 while True 循环
  - [x] SubTask 4.3: 在思考后、行动前添加反馈检查点（_check_feedback 方法）
  - [x] SubTask 4.4: 实现5种反馈类型的处理逻辑
  - [x] SubTask 4.5: 在检查点发出 feedback_request SSE事件
  - [x] SubTask 4.6: 在反馈处理后发出 feedback_accepted SSE事件
  - [x] SubTask 4.7: 处理 execution_termination 反馈时立即终止循环

- [x] Task 5: 修改react_stream透传反馈事件
  - [x] SubTask 5.1: 在 `backend/app/services/qa/react_stream.py` 中添加 feedback_request 事件的透传
  - [x] SubTask 5.2: 添加 feedback_accepted 事件的透传

- [x] Task 6: 添加反馈API端点
  - [x] SubTask 6.1: 在 `backend/app/api/routes.py` 中添加 POST /api/human-feedback 端点
  - [x] SubTask 6.2: 添加 GET /api/human-feedback/{session_id} 端点
  - [x] SubTask 6.3: 添加 GET /api/human-feedback-statistics 端点

- [x] Task 7: 创建前端反馈输入组件
  - [x] SubTask 7.1: 创建 `frontend/src/components/gen-ui/HumanFeedbackInput.vue`
  - [x] SubTask 7.2: 实现反馈类型选择器（5种类型）
  - [x] SubTask 7.3: 实现反馈文本输入
  - [x] SubTask 7.4: 实现工具调用建议的专用输入（工具名+参数）
  - [x] SubTask 7.5: 实现参数调整的专用输入
  - [x] SubTask 7.6: 实现一键终止按钮
  - [x] SubTask 7.7: 实现反馈提交到后端API的逻辑

- [x] Task 8: 修改ReActThinkingDisplay集成步骤级反馈
  - [x] SubTask 8.1: 在action步骤旁添加反馈按钮
  - [x] SubTask 8.2: 点击按钮展开HumanFeedbackInput面板
  - [x] SubTask 8.3: 预填当前步骤的工具名和参数

- [x] Task 9: 修改ChatView集成反馈交互
  - [x] SubTask 9.1: 处理 feedback_request SSE事件，显示反馈输入提示
  - [x] SubTask 9.2: 处理 feedback_accepted SSE事件，更新反馈状态显示
  - [x] SubTask 9.3: 在ReAct运行时显示全局终止按钮

- [x] Task 10: 创建反馈历史页面
  - [x] SubTask 10.1: 创建 `frontend/src/components/gen-ui/FeedbackHistory.vue` 组件
  - [x] SubTask 10.2: 创建 `frontend/src/views/FeedbackHistoryView.vue` 页面
  - [x] SubTask 10.3: 在 `frontend/src/router/index.js` 中添加 /feedback-history 路由

# Task Dependencies
- [Task 2] depends on [Task 1] (类型定义引用模型)
- [Task 3] depends on [Task 1] (服务使用模型)
- [Task 4] depends on [Task 2, Task 3] (AgentLoop使用类型和服务)
- [Task 5] depends on [Task 4] (透传AgentLoop发出的事件)
- [Task 6] depends on [Task 3] (API调用服务)
- [Task 7] depends on [Task 6] (前端调用API)
- [Task 8] depends on [Task 7] (使用反馈输入组件)
- [Task 9] depends on [Task 5, Task 7] (处理SSE事件和使用组件)
- [Task 10] depends on [Task 6] (查询API)
- [Task 1, Task 2] 可并行执行
- [Task 7, Task 10] 部分可并行（Task 10不依赖Task 7-9）
