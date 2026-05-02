# Tasks - DeepSeek 思考模式完整实现

## 任务列表

- [x] Task 1: 修改后端数据模型和配置
  - [x] 1.1 在 `QARequest` 中新增 `reasoning_effort` 字段（[routes.py](backend/app/api/routes.py)）
  - [x] 1.2 在 `LLMConfig` 中新增 `reasoning_effort` 字段，默认值为 "high"（[llm_client.py](backend/app/agents/llm_client.py)）
  - [x] 1.3 更新 `appStore.js` 的默认 params，添加 `reasoning_effort: 'high'`（[appStore.js](frontend/src/stores/appStore.js)）

- [x] Task 2: 修改后端 LLMClient 支持思考模式参数
  - [x] 2.1 修改 `_openai_chat_kwargs` 方法，支持通过 `extra_body` 传递 thinking 参数
  - [x] 2.2 添加 `reasoning_effort` 参数传递逻辑
  - [x] 2.3 确保思考模式下不传递 temperature/top_p 等不兼容参数
  - [x] 2.4 验证流式响应正确返回 reasoning_content

- [x] Task 3: 实现前端思考强度调节 UI 组件
  - [x] 3.1 创建 ThinkingEffortSelector.vue 组件（类似图片中的 toggle + 弹出选项面板样式）
  - [x] 3.2 实现 4 个选项：Low/Medium/High/Max，每个选项包含图标、标题、描述
  - [x] 3.3 实现点击 toggle 按钮弹出/关闭选项面板的交互逻辑
  - [x] 3.4 实现选项选择后的状态更新和按钮文字变更
  - [x] 3.5 支持 ESC 键关闭、点击外部关闭等交互细节

- [x] Task 4: 集成思考强度选择器到 ChatView
  - [x] 4.1 在输入区域 Thinking 按钮旁边添加 ThinkingEffortSelector 组件
  - [x] 4.2 修改 `sendStream` 方法，在请求中包含 `reasoning_effort` 参数
  - [x] 4.3 确保 Thinking 按钮和强度选择器的状态同步
  - [x] 4.4 在参数设置侧边栏中显示当前思考模式和强度信息

- [x] Task 5: 实现正确的多轮对话拼接逻辑
  - [x] 5.1 修改后端 QA 服务，记录每轮是否进行了工具调用
  - [x] 5.2 实现非工具调用轮次的 reasoning_content 过滤逻辑
  - [x] 5.3 实现工具调用轮次的完整 reasoning_content 回传逻辑
  - [x] 5.4 前端维护对话历史时，根据工具调用标记决定是否保留 reasoning_content

- [x] Task 6: 测试和验证
  - [x] 6.1 测试思考模式开关的启用/禁用功能
  - [x] 6.2 测试不同思考强度等级的切换和传递
  - [x] 6.3 测试非工具调用的多轮对话（验证 reasoning_content 不回传）
  - [x] 6.4 测试工具调用的多轮对话（验证 reasoning_content 正确回传）
  - [x] 6.5 测试流式响应中 reasoning_content 的实时显示
  - [x] 6.6 验证思考模式下不传递 temperature 等不兼容参数

## Task Dependencies
- Task 1 必须首先完成（基础数据结构）
- Task 2 依赖 Task 1（需要数据模型支持）
- Task 3 可与 Task 2 并行开发（UI 组件独立）
- Task 4 依赖 Task 3（需要组件就绪）
- Task 5 依赖 Task 2 和 Task 4（需要后端支持和前端集成）
- Task 6 依赖所有前序任务完成
