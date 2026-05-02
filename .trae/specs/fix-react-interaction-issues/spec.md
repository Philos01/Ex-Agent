# 修复 ReAct 模式交互问题 Spec

## Why
用户报告两个关键交互缺陷：
1. **ReAct 提示弹窗持续显示**：即使勾选"不再显示此提示"，弹窗仍然反复出现
2. **ModeSelector 组件自动收起**：关闭 ReAct 弹窗后，模式选择器面板意外收起，导致用户无法完成操作

这两个问题严重影响用户体验，需要立即修复。

## What Changes
- **修复 ReActModePrompt 的持久化逻辑**
  - 确保"不再显示此提示"选项正确保存到 localStorage
  - 在触发提示前必须先检查 localStorage 状态
  
- **修复 ModeSelector 的点击外部关闭逻辑**
  - 排除 ReAct 弹窗区域的点击事件
  - 防止弹窗关闭时误触发表板收起

- **优化 ChatView.vue 的事件处理**
  - 在所有触发 showReActPrompt 的位置添加 checkShouldShow 检查
  - 确保逻辑一致性

## Impact
- Affected specs: implement-deepseek-thinking-mode (补充修复)
- Affected code:
  - [ChatView.vue](frontend/src/views/ChatView.vue) - 事件处理逻辑
  - [ModeSelector.vue](frontend/src/components/gen-ui/ModeSelector.vue) - 点击外部检测
  - [ReActModePrompt.vue](frontend/src/components/gen-ui/ReActModePrompt.vue) - 已有实现验证

## ADDED Requirements

### Requirement: ReAct 提示持久化功能正常工作
系统 SHALL 确保"不再显示此提示"选项能够正确阻止弹窗再次显示。

#### Scenario: 用户勾选"不再显示"并关闭弹窗
- **WHEN** 用户勾选"不再显示此提示"复选框并点击"知道了"
- **THEN** localStorage 中保存 `react_prompt_dismissed = 'true'`
- **AND** 后续启用 ReAct 模式时不再弹出提示

#### Scenario: 用户未勾选"不再显示"
- **WHEN** 用户直接点击"知道了"关闭弹窗（未勾选复选框）
- **THEN** 下次启用 ReAct 时仍会弹出提示

#### Scenario: 多次切换 ReAct 模式
- **WHEN** 用户已禁用提示后多次启用/禁用 ReAct
- **THEN** 弹窗始终不出现（除非手动清除 localStorage）

### Requirement: ModeSelector 面板不受弹窗关闭影响
系统 SHALL 确保 ReAct 弹窗的关闭操作不会导致 ModeSelector 面板意外收起。

#### Scenario: 从 ModeSelector 启用 ReAct 并关闭提示弹窗
- **WHEN** 用户在 ModeSelector 面板中点击"ReAct 多步推理"选项
- **AND** 弹出 ReAct 提示弹窗
- **AND** 用户点击"知道了"关闭弹窗
- **THEN** ModeSelector 面板保持展开状态
- **AND** 用户可以看到 ReAct 选项已被选中（蓝色高亮）

#### Scenario: 点击弹窗背景遮罩层
- **WHEN** 用户点击 ReAct 弹窗的半透明背景区域关闭弹窗
- **THEN** ModeSelector 面板保持展开状态不变

## MODIFIED Requirements

### Requirement: ChatView.vue 中的 ReAct 触发逻辑
修改以下函数，确保在显示提示前检查 localStorage：

```javascript
// 修改前（错误）
const toggleReAct = () => {
  const newVal = !params.value.use_react
  params.value.use_react = newVal
  updateParams()
  
  if (newVal && promptRef.value && promptRef.value.checkShouldShow()) {
    showReActPrompt.value = true  // 问题：即使返回 false 也可能被其他逻辑覆盖
  }
}

// 修改后（正确）
const toggleReAct = () => {
  const newVal = !params.value.use_react
  params.value.use_react = newVal
  updateParams()
  
  // 只有当用户未禁用提示时才显示
  if (newVal && promptRef.value && promptRef.value.checkShouldShow()) {
    showReActPrompt.value = true
  }
}

// 新增：统一的 ReAct 提示显示函数
const shouldShowReActPrompt = () => {
  return promptRef.value ? promptRef.value.checkShouldShow() : true
}
```

### Requirement: ModeSelector.vue 的点击外部检测
修改 handleClickOutside 函数，排除模态弹窗：

```javascript
// 修改前（错误）
const handleClickOutside = (e) => {
  if (selectorRef.value && !selectorRef.value.contains(e.target)) {
    closePanel()  // 问题：弹窗关闭时的点击也会触发这里
  }
}

// 修改后（正确）
const handleClickOutside = (e) => {
  // 如果点击的是模态弹窗或其内部元素，不关闭面板
  const target = e.target
  const isModalClick = target.closest('.fixed.inset-0') || 
                       target.closest('[class*="backdrop"]') ||
                       target.closest('[class*="modal"]')
  
  if (isModalClick) return
  
  // 正常的外部点击检测
  if (selectorRef.value && !selectorRef.value.contains(target)) {
    closePanel()
  }
}
```

## REMOVED Requirements
无

## Technical Notes

### 问题根因分析

**问题1：弹窗持续显示**
- 根因：ChatView.vue 中的 `handleReActToggleWithPrompt` 和 `handleReActPromptFromModeSelector` 函数没有调用 `checkShouldShow()` 检查
- 影响：即使用户已勾选"不再显示"，这些函数仍会强制设置 `showReActPrompt.value = true`
- 位置：[ChatView.vue#L704-L712](frontend/src/views/ChatView.vue#L704-L712)

**问题2：ModeSelector 自动收起**
- 根因：ModeSelector 监听 document 级别的 click 事件
- 影响：当用户点击 ReAct 弹窗的"知道了"按钮时，click 事件冒泡到 document，触发 handleClickOutside
- 位置：[ModeSelector.vue#handleClickOutside](frontend/src/components/gen-ui/ModeSelector.vue)

### 修复策略

1. **防御性编程**：在所有设置 `showReActPrompt = true` 前添加守卫条件
2. **事件隔离**：ModeSelector 的外部点击检测应排除模态弹窗区域
3. **用户体验优先**：确保操作流程连贯，不会因辅助 UI 元素干扰主要任务
