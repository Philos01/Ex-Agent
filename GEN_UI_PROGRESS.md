# Ex-Agent Gen UI 开发进度文档

> 开发起始日期：2026-04-11

---

## 第一阶段：RAG 思考过程可视化 ✨ (已完成)

**目标**：让 RAG 从"黑盒"变成"白盒"，动态展示思考链路

- [x] 创建 Gen UI 开发进度文档
- [x] 后端：修改 qa.py 增加 state 事件输出（retrieving、analyzing、generating、done）
- [x] 后端：修改 routes.py 的 event_generator 发送 state 事件
- [x] 前端：创建 ThinkingSteps.vue 组件
- [x] 前端：修改 ChatView.vue 集成 ThinkingSteps 组件
- [x] 前端：修改消息数据结构，增加 thinkingState 字段
- [x] 修复：让思考过程卡片一直显示
- [x] 修复：生成完毕后停止旋转动画
- [ ] 测试：验证完整的思考过程可视化流程

---

## 第二阶段：深度引用交互 📚 (已完成核心开发)

**目标**：实现类似 Perplexity 的引用体验

- [x] 后端：增强 sources 数据结构，增加文档 chunk 的位置和内容信息（已有 chunk_index）
- [x] 后端：新增 `/api/document/preview` 端点，支持按位置获取文档片段
- [x] 前端：创建 CitationHoverCard.vue 组件（悬停预览卡片）
- [x] 前端：创建 DocumentPreviewPanel.vue 组件（右侧文档预览面板）
- [x] 前端：修改引用源卡片，添加点击预览功能
- [x] 测试：验证引用悬停和预览功能

---

## 第三阶段：结构化数据可视化 📊 (已完成核心开发)

**目标**：将科研数据渲染成交互式表格/图表

- [x] 后端：在 Pydantic 中定义数据结构 Schema
- [x] 前端：创建 DataTable.vue 组件（支持导出 CSV）
- [x] 前端：创建 DataChart.vue 组件（原生 Canvas，支持柱状图和折线图）
- [x] 前端：创建 ComponentRegistry.js 组件注册表
- [x] 前端：修改 ChatView.vue 支持动态组件渲染
- [x] 前端：添加测试按钮和模拟数据
- [ ] 测试：验证表格和图表渲染
- [ ] 后端：集成 Function Calling 机制

---

## SSE 协议扩展说明（补充）

### 新增事件类型（阶段三）
- `component`: 动态组件渲染

```json
{
  "type": "component",
  "component": "DataTable",
  "props": {
    "columns": ["催化剂", "产率", "温度"],
    "data": [
      ["催化剂A", "85%", "80°C"],
      ["催化剂B", "92%", "90°C"]
    ]
  }
}
```

### 组件类型
- `DataTable`: 数据表格
- `DataChart`: 数据图表

---

## 第四阶段：对话驱动的系统控制 🎛️ (待开始)

**目标**：让用户通过对话直接控制系统

- [ ] 后端：新增 intent_detection 模块
- [ ] 后端：新增可通过对话调用的 API 集合
- [ ] 后端：SSE 新增 action 事件类型
- [ ] 前端：创建 ActionButtons.vue 组件
- [ ] 前端：实现按钮点击调用后端 API
- [ ] 测试：验证对话驱动控制功能

---

## SSE 协议扩展说明

### 现有事件类型
- `content`: 文本内容
- `sources`: 引用来源

### 新增事件类型（阶段一）
- `state`: 思考状态更新

```json
{
  "type": "state",
  "phase": "retrieving",
  "message": "正在连接 Chroma 向量库...",
  "progress": 25
}
```

### Phase 枚举值
- `retrieving`: 检索阶段
- `analyzing`: 分析阶段  
- `generating`: 生成阶段
- `done`: 完成
