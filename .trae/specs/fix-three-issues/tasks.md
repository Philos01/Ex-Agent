
# 修复三大功能异常 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: 在数据库模型中添加react_steps字段
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查现有消息模型结构
  - 添加react_steps JSON字段
  - 注册到models/__init__.py
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: HumanFeedback模型已创建并注册
  - `human-judgement` TR-1.2: 数据库表结构检查
- **Notes**: 使用现有BaseModel结构

## [x] Task 2: 修改ChatView修复store监听逻辑
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改ChatView.vue的store监听
  - 移除无条件清空reactSteps的代码
  - 增加是否切换会话的判断逻辑
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `human-judgement` TR-2.1: 只在真正切换会话时清空
  - `human-judgement` TR-2.2: 状态同步正常
- **Notes**: 保持现有状态结构，增加会话检测

## [x] Task 3: 实现AbortController终止功能
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 在ChatView.vue中添加currentAbortController
  - 修改handleTerminateAgent
  - 修改sendStream函数使用AbortController
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgement` TR-3.1: 点击终止立即停止fetch
  - `human-judgement` TR-3.2: 状态立即更新
- **Notes**: 保持错误处理

## [x] Task 4: 改进AgentLoop终止反馈处理
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 确保EXECUTION_TERMINATION立即返回
  - 检查现有代码已正确实现
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 收到终止反馈立即停止
- **Notes**:

## [x] Task 5: 完善人类反馈等待机制
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 在AgentLoop中增加等待逻辑
  - 改进反馈服务，支持阻塞等待
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `human-judgement` TR-5.1: 发送FEEDBACK_REQUEST后等待用户输入
  - `human-judgement` TR-5.2: 反馈提交后被立即处理
- **Notes**: 实现0.5秒超时，避免卡死

## [x] Task 6: 持久化reactSteps到数据库
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改session_service.py支持保存reactSteps
  - 修改API接口传递reactSteps
  - 修改前端同步保存
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-6.1: 保存时包含reactSteps
  - `programmatic` TR-6.2: 读取时恢复reactSteps
  - `human-judgement` TR-6.3: 刷新页面思考链路恢复
- **Notes**: 支持JSON字段

