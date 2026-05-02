# Tasks - 修复 ReAct 模式交互问题

## 任务列表

- [x] Task 1: 修复 ChatView.vue 中的 ReAct 提示触发逻辑
  - [x] 1.1 修改 `toggleReAct` 函数，确保正确检查 `checkShouldShow()` 返回值
  - [x] 1.2 修改 `handleReActToggleWithPrompt` 函数，添加守卫条件防止强制显示提示
  - [x] 1.3 修改 `handleReActPromptFromModeSelector` 函数，添加守卫条件
  - [x] 1.4 创建统一的 `shouldShowReActPrompt` 辅助函数，统一判断逻辑

- [x] Task 2: 修复 ModeSelector.vue 的点击外部检测逻辑
  - [x] 2.1 修改 `handleClickOutside` 函数，排除模态弹窗区域的点击事件
  - [x] 2.2 添加对 fixed 定位元素、backdrop、modal 类名的检测
  - [x] 2.3 确保点击 ReAct 弹窗（包括背景遮罩）不会触发表板关闭
  - [x] 2.4 测试多种场景：点击弹窗按钮、点击遮罩、按 ESC 关闭弹窗

- [x] Task 3: 验证和测试
  - [x] 3.1 测试场景1：勾选"不再显示"后多次切换 ReAct 模式，验证不再弹出
  - [x] 3.2 测试场景2：不勾选"不再显示"，验证每次启用都弹出
  - [x] 3.3 测试场景3：从 ModeSelector 启用 ReAct → 弹出提示 → 关闭提示 → 验证面板保持展开
  - [x] 3.4 测试场景4：清除 localStorage 后重新测试完整流程
  - [x] 3.5 验证 localStorage 键值正确保存和读取

## Task Dependencies
- Task 1 和 Task 2 可以并行开发（相互独立）
- Task 3 依赖 Task 1 和 Task 2 完成
