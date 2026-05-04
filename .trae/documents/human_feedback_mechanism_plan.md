# Agent系统人类反馈机制实现计划

## 1. 概述

本计划旨在为现有的Agent系统添加完整的人类反馈机制，使用户能够在Agent执行过程中提供实时指导，同时移除ReAct模式的迭代限制。

### 1.1 核心功能

- **实时反馈输入**：用户在Agent执行过程中提供反馈
- **工具调用干预**：指示Agent调用特定工具或调整工具参数
- **执行控制**：终止当前操作或修改执行策略
- **反馈历史记录**：保存和查询人类反馈历史
- **无限制迭代**：移除ReAct模式的5次迭代限制，支持无限次执行（通过人类反馈控制）

## 2. 系统架构设计

### 2.1 主要模块

1. **反馈模型层**：定义反馈数据结构
2. **反馈服务层**：处理反馈的存储和查询
3. **反馈API层**：提供HTTP接口
4. **Agent集成层**：在Agent执行循环中集成反馈机制
5. **前端UI层**：用户交互界面

### 2.2 通信机制设计

反馈机制采用 **实时双向通信** 架构，基于现有的SSE（Server-Sent Events）流进行扩展：

#### 2.2.1 通信通道

1. **下行通道（后端→前端）**：
   - 复用现有的SSE流
   - 新增 `feedback_request` 事件类型，通知用户可以提供反馈
   - 新增 `feedback_accepted` 事件类型，通知用户反馈已被应用

2. **上行通道（前端→后端）**：
   - 使用HTTP POST接口提交反馈
   - 反馈通过会话ID（session_id）与执行中的Agent关联

#### 2.2.2 反馈队列管理

- 每个会话维护一个反馈队列
- 队列按时间顺序存储未处理的反馈
- Agent在检查点从队列中取出并处理反馈
- 已处理的反馈标记为已应用

#### 2.2.3 会话状态同步

- 使用会话ID作为关键关联标识
- 前端维护当前会话的反馈状态
- 后端通过API提供反馈状态查询

#### 2.2.4 异步处理流程

```
用户在UI上提交反馈 → 前端POST /api/feedback → 
后端存储反馈并加入会话队列 → Agent在检查点检查队列 → 
处理反馈 → 发送feedback_accepted事件 → 前端更新UI
```

## 3. 实现步骤

### 步骤1：定义数据模型和类型

在 `backend/app/models/` 下创建新的反馈模型文件 `human_feedback.py`

```python
# 主要数据结构
- HumanFeedback (反馈记录)
- FeedbackType (反馈类型枚举)
  - TOOL_CALL_SUGGESTION (建议工具调用)
  - PARAMETER_ADJUSTMENT (参数调整)
  - EXECUTION_TERMINATION (终止执行)
  - STRATEGY_MODIFICATION (策略修改)
  - GENERAL_COMMENT (一般评论)
```

### 步骤2：实现反馈服务

在 `backend/app/services/` 下创建 `human_feedback_service.py`

* 存储和查询反馈记录

* 关联反馈与会话

* 提供反馈统计功能

### 步骤3：扩展Agent类型定义

在 `backend/app/agents/types.py` 中添加：

* FeedbackRequest

* FeedbackResponse

* FeedbackState（反馈状态：等待/接受/拒绝）

### 步骤4：修改AgentLoop实现

修改 `backend/app/agents/agent_loop.py`：

- 在关键节点（思考/行动前）插入反馈检查点
- 实现反馈处理逻辑
- 支持反馈对执行流程的影响
- **移除5次迭代的硬限制**，实现无限迭代模式
- 添加合理的终止条件（通过人类反馈或AI自判断）

### 步骤5：添加API端点

在 `backend/app/api/routes.py` 中添加：

* POST /api/feedback - 提交反馈

* GET /api/feedback/{session\_id} - 获取会话反馈历史

* GET /api/feedback/statistics - 获取反馈统计

### 步骤6：前端UI集成

修改 `frontend/src/views/ChatView.vue`：

* 添加反馈输入界面

* 在ReAct执行过程中显示反馈按钮

* 展示反馈历史记录

* 添加反馈历史页面组件

### 步骤7：在ReActThinkingDisplay组件中集成反馈

修改 `frontend/src/components/gen-ui/ReActThinkingDisplay.vue`：

* 在每个执行步骤旁添加反馈按钮

* 支持参数调整界面

* 提供终止执行按钮

## 4. 数据库迁移

### 4.1 新增表

```sql
-- 人类反馈记录表
CREATE TABLE IF NOT EXISTS human_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id TEXT,
    feedback_type TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_name TEXT,
    tool_parameters TEXT,
    is_applied BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT (datetime('now')),
    user_id TEXT
);
```

## 5. 反馈处理流程

```
用户请求 → Agent开始执行 → 检查反馈点 → 有新反馈？
                    ↓ 是
              处理反馈 → 调整执行 → 继续
                    ↓ 否
              继续执行 → 下一个检查点
```

## 6. 关键功能详细设计

### 6.1 反馈类型处理

1. **TOOL\_CALL\_SUGGESTION**：

   * 接受工具名和参数

   * 覆盖Agent的原始工具调用决策

2. **PARAMETER\_ADJUSTMENT**：

   * 修改即将调用工具的参数

   * 支持参数验证

3. **EXECUTION\_TERMINATION**：

   * 立即停止当前执行

   * 返回部分结果或用户指定内容

4. **STRATEGY\_MODIFICATION**：

   * 改变Agent的思考/行动策略

   * 如调整最大迭代次数、改变检索策略等

### 6.2 检查点设置

在以下关键节点设置反馈检查：

* 每次思考（thought）后

* 每次行动（action）前

* 每次观察（observation）后

## 7. 文件清单

### 后端（backend/app/）

* models/human\_feedback.py  \[新建]

* services/human\_feedback\_service.py  \[新建]

* agents/types.py  \[修改]

* agents/agent\_loop.py  \[修改]

* api/routes.py  \[修改]

### 前端（frontend/src/）

* views/ChatView\.vue  \[修改]

* components/gen-ui/ReActThinkingDisplay.vue  \[修改]

* components/gen-ui/HumanFeedbackInput.vue  \[新建]

* components/gen-ui/FeedbackHistory.vue  \[新建]

* views/FeedbackHistoryView\.vue  \[新建]

* router/index.js  \[修改]

## 8. 依赖检查

无需新增外部依赖，使用现有技术栈即可实现。

## 9. 风险与注意事项

1. **性能影响**：频繁检查反馈可能影响执行速度 - 通过异步检查优化
2. **用户体验**：确保反馈机制不会过度干扰正常流程
3. **数据一致性**：确保反馈记录与执行状态正确关联

## 10. 测试计划

* 单元测试：反馈服务逻辑

* 集成测试：Agent与反馈机制的集成

* 用户体验测试：前端交互流程

