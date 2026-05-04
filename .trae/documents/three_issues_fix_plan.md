
# 三大功能异常修复计划

## 问题调研结论

通过深入分析代码库，已定位到三个问题的根源：

### 1. 思考链路持续性问题
- **问题根因1**：在 `ChatView.vue` 第562-563行，当 `store.chatMessages` 变化时，会无条件重置 `reactSteps` 和 `isReActRunning`，导致正在运行的思考链路被清空
- **问题根因2**：reactSteps只保存在内存中，刷新页面后丢失
- **问题根因3**：数据库中的消息表没有保存reactSteps字段

### 2. 人类反馈机制问题
- **问题根因1**：AgentLoop在发送 `FEEDBACK_REQUEST` 后没有真正"暂停"等待反馈，只是发送事件后继续执行
- **问题根因2**：反馈队列机制存在但没有等待机制，AgentLoop不会阻塞等待用户输入

### 3. 终止按钮功能失效
- **问题根因1**：`handleTerminateAgent` 只发送 `execution_termination` 反馈，但没有真正取消fetch请求
- **问题根因2**：fetch请求没有使用 `AbortController` 进行控制

---

## 修复方案

### 第一阶段：修复思考链路长期持久化（优先级最高）

**修改文件**：
- `backend/app/models/message.py` （新增）
- `backend/app/models/__init__.py`
- `backend/app/services/session_service.py`
- `frontend/src/views/ChatView.vue`
- `frontend/src/store/index.js`

**修改内容**：
1. 在数据库消息表中添加 `react_steps` JSON字段
2. 修改保存消息的API，将reactSteps持久化
3. 修改ChatView.vue：只在真正会话切换时清空，其他情况保留
4. 页面加载时从数据库恢复reactSteps

### 第二阶段：实现AbortController和立即终止

**修改文件**：
- `frontend/src/views/ChatView.vue`
- `backend/app/agents/agent_loop.py`

**修改内容**：
1. 前端使用AbortController控制fetch请求
2. 终止按钮同时发送反馈和取消fetch
3. 后端AgentLoop收到termination反馈后立即终止

### 第三阶段：完善人类反馈机制

**修改文件**：
- `backend/app/agents/agent_loop.py`
- `backend/app/services/human_feedback_service.py`
- `frontend/src/views/ChatView.vue`

**修改内容**：
1. 实现真正的等待机制：AgentLoop在发送FEEDBACK_REQUEST后等待（带超时）
2. 反馈提交后立即被AgentLoop处理

---

## 详细修复步骤

### 步骤1：在数据库中支持reactSteps持久化

1.1 修改消息模型，添加react_steps字段（在message.py中）
```python
react_steps = Column(JSON, nullable=True)  # 保存ReAct执行步骤
```

1.2 修改session_service.py中的save_message方法
```python
def save_message(self, session_id: str, role: str, content: str, 
                 sources: Optional[List[Dict]] = None,
                 react_steps: Optional[List[Dict]] = None)
```

1.3 修改API接口，支持保存reactSteps

### 步骤2：修复思考链路被清空的问题

2.1 修改ChatView.vue的watch监听
```javascript
// 监听store中chatMessages的变化，同步到本地
watch(() => store.chatMessages, (newMessages) => {
  if (isSyncingWithStore.value) return
  isSyncingWithStore.value = true
  console.log('[DEBUG] store.chatMessages changed:', newMessages.length, 'messages')
  
  // 保存本地的状态（按消息ID）
  const localThinkingStates = {}
  const localReactSteps = {}
  messages.value.forEach(msg => {
    if (msg.thinkingState) localThinkingStates[msg.id] = msg.thinkingState
    if (msg.reactSteps) localReactSteps[msg.id] = msg.reactSteps
  })
  
  // 完全替换为新的消息列表，但保留匹配的状态
  messages.value = newMessages.map(storeMsg => {
    const localMsg = { ...storeMsg }
    if (localThinkingStates[storeMsg.id]) localMsg.thinkingState = localThinkingStates[storeMsg.id]
    if (localReactSteps[storeMsg.id]) localMsg.reactSteps = localReactSteps[storeMsg.id]
    return localMsg
  })
  
  // 检查是否是真正的会话切换：检查第一个消息ID是否不同
  const oldFirstId = store.chatMessages[0]?.id
  const newFirstId = newMessages[0]?.id
  const isSessionSwitch = oldFirstId !== newFirstId
  
  // 只有真正的会话切换时才重置全局ReAct状态
  if (isSessionSwitch) {
    console.log('[DEBUG] Session switch detected, resetting ReAct state')
    reactSteps.value = []
    isReActRunning.value = false
  }
  
  // 如果是空数组，说明是新建会话或切换到了空会话，重置UI
  if (newMessages.length === 0) {
    resetUI()
  }
  
  nextTick(() => {
    isSyncingWithStore.value = false
  })
}, { deep: true })
```

2.2 每次更新reactSteps时，同步更新到messages对象
```javascript
// 在处理react_thought/react_action等事件后
const lastIndex = messages.value.length - 1
if (lastIndex &gt;= 0) {
  messages.value[lastIndex].reactSteps = [...reactSteps.value]
  // 持久化到store（可选）
}
```

### 步骤3：实现AbortController控制fetch请求

3.1 在ChatView.vue中添加abort controller
```javascript
let currentAbortController = null

const handleTerminateAgent = async () =&gt; {
  console.log('[DEBUG] Terminating agent execution')
  
  // 1. 发送终止反馈
  const sessionId = store.currentSessionId || 'default'
  try {
    await fetch('/api/human-feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        feedback_type: 'execution_termination',
        content: '用户终止执行'
      })
    })
  } catch (e) {
    console.error('[DEBUG] Failed to send termination feedback:', e)
  }
  
  // 2. 立即取消fetch请求
  if (currentAbortController) {
    currentAbortController.abort()
    console.log('[DEBUG] Fetch request aborted')
  }
  
  // 3. 立即重置前端状态
  isReActRunning.value = false
  loading.value = false
  streaming.value = false
}
```

3.2 在sendStream函数中使用AbortController
```javascript
const sendStream = async () =&gt; {
  // ... 之前的代码 ...
  
  // 创建abort controller
  currentAbortController = new AbortController()
  const signal = currentAbortController.signal
  
  try {
    const response = await fetch('/api/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({...}),
      signal: signal // 添加信号
    })
    
    // ... 后续代码 ...
  } catch (e) {
    if (e.name === 'AbortError') {
      console.log('[DEBUG] Fetch aborted by user')
      // 处理终止状态
      isReActRunning.value = false
      loading.value = false
      streaming.value = false
      return
    }
    // ... 其他错误处理 ...
  } finally {
    currentAbortController = null
  }
}
```

### 步骤4：AgentLoop立即终止机制

4.1 在收到EXECUTION_TERMINATION后立即终止
```python
if feedback.feedback_type == FeedbackType.EXECUTION_TERMINATION:
    logger.info("[AgentLoop] Execution terminated by human feedback, stopping immediately")
    self.scratchpad.add_step(thought=parsed.thought)
    yield AgentEvent(...)
    yield AgentEvent(...)
    return  # 立即返回，不继续执行
```

---

## 预期效果

1. **思考链路长期持久化**：
   - 刷新页面后，思考链路完整保留
   - 只有真正切换会话时才会清空状态
   - 切换窗口不会影响正在执行的链路

2. **终止按钮功能正常**：
   - 点击后立即停止fetch请求
   - 前端状态立即更新
   - 同时发送终止反馈给后端

3. **人类反馈机制**：
   - Agent发送feedback_request后会等待用户输入
   - 提交的反馈能立即被Agent处理

---

## 修复顺序

1. **先实现数据库持久化reactSteps**（最关键，解决长期存在问题）
2. **修复ChatView的状态重置逻辑**（解决切换窗口清空问题）
3. **再实现终止按钮功能**（第二优先级）
4. **最后完善人类反馈等待机制**（第三优先级）

