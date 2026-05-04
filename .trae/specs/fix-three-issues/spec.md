
# 修复三大功能异常 - Product Requirement Document

## Overview
- **Summary**: 修复Agent系统中的三个关键问题：思考链路持续性、人类反馈机制、终止按钮失效。
- **Purpose**: 解决用户反馈的核心痛点，提升系统稳定性和用户体验。
- **Target Users**: 所有使用Agent系统的用户。

## Goals
- **思考链路长期持久化**：刷新页面后思考链路完整保留，切换窗口不影响。
- **终止按钮功能正常**：点击立即停止执行，前端状态立即更新。
- **人类反馈机制可用**：Agent在需要时暂停等待用户输入。

## Non-Goals (Out of Scope)
- 完全重构Agent架构（保持现有架构）。
- 添加新的工具或Agent模式。
- 优化性能或重构代码风格（仅修复问题）。

## Background & Context
系统现有问题：
1. ChatView.vue中store更新时会无条件清空reactSteps
2. reactSteps仅保存在内存，刷新丢失
3. 终止按钮没有使用AbortController
4. AgentLoop没有等待机制
5. 数据库消息表没有react_steps字段

## Functional Requirements
- **FR-1**: 数据库支持持久化react_steps。
- **FR-2**: 切换会话时才清空reactSteps，其他情况保留。
- **FR-3**: 终止按钮使用AbortController立即取消请求。
- **FR-4**: 执行termination反馈时立即终止。
- **FR-5**: AgentLoop支持等待人类反馈。

## Non-Functional Requirements
- **NFR-1**: 所有现有功能保持正常。
- **NFR-2**: 修复后不引入新bug。
- **NFR-3**: 性能无明显下降。

## Constraints
- **Technical**: 保持现有技术栈（Vue 3, Python/FastAPI, SQLite）。
- **Business**: 本次修复不引入新功能。
- **Dependencies**: 无外部依赖新增。

## Assumptions
- 现有数据库结构支持添加新字段。
- 现有ReactAgent和AgentLoop架构可正常工作。
- 用户环境支持AbortController API。

## Acceptance Criteria

### AC-1: 数据库支持持久化react_steps
- **Given**: 数据库表结构
- **When**: 消息保存到数据库
- **Then**: react_steps字段被保存
- **Verification**: `programmatic`
- **Notes**: 测试保存和读取功能

### AC-2: 思考链路不会被意外清空
- **Given**: Agent正在执行中，用户切换窗口或进行其他操作
- **When**: store.chatMessages更新
- **Then**: 仅在真正会话切换时清空reactSteps
- **Verification**: `human-judgment`

### AC-3: 终止按钮功能正常
- **Given**: Agent正在执行，用户点击终止
- **When**: handleTerminateAgent被调用
- **Then**: fetch立即取消，状态立即更新
- **Verification**: `human-judgment`

### AC-4: 终止反馈被立即处理
- **Given**: 执行终止反馈
- **When**: AgentLoop收到EXECUTION_TERMINATION
- **Then**: 立即返回终止
- **Verification**: `programmatic`

### AC-5: 刷新页面后思考链路恢复
- **Given**: 页面刷新
- **When**: 页面加载
- **Then**: reactSteps从数据库恢复
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要处理session_service中的已有代码？（是，需要修改）

