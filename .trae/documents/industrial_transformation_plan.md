# 工业级 Agent 改造计划

## 一、现状分析

### 1.1 当前系统架构优势（可借鉴）
- ✅ **人类反馈机制** (`HumanFeedbackService`) - 已有基础
- ✅ **审计日志** (`AuditLog`) - 已实现
- ✅ **权限模型** (`Permission`) - 已搭建框架
- ✅ **参数验证** (`ParameterValidator`) - 已有基础
- ✅ **Agent 执行引擎** (`AgentLoop` / `ReActAgent`) - 模块化设计
- ✅ **技能执行器** (`SkillExecutor`) - 支持外部工具调用
- ✅ **错误处理** - 已有基本错误分类和处理

### 1.2 当前系统不足（需改造）
- ❌ **边缘控制缺失** - 没有离线降级策略
- ❌ **闭环不完整** - 缺少执行确认、失败重试、回滚机制
- ❌ **LLM 提案-审批流程不完善** - 只有反馈，没有明确的"提案→审批→执行"
- ❌ **幻觉防护不足** - 缺少 RAG 验证、不确定禁止执行、决策留痕
- ❌ **工程化能力弱** - 缺少协议对接、脏数据处理、异常检测、设备适配
- ❌ **安全机制不完善** - 缺少操作分级权限、高危操作二次确认

---

## 二、工业级改造方案

### 2.1 架构改造：边缘控制 + 降级 + 规则系统

#### 新增模块：`EdgeController`
```
backend/app/core/edge_controller.py
```
**功能：**
- 网络状态检测（断网监控）
- 离线模式自动切换
- 规则系统集成（预定义规则作为 LLM 降级方案）
- 本地缓存策略

#### 新增模块：`RuleEngine`
```
backend/app/core/rule_engine.py
```
**功能：**
- 规则定义 DSL
- 规则匹配引擎
- 规则版本管理
- 规则执行审计

#### 修改配置：`config.json.example`
新增配置项：
```json
{
  "edge": {
    "enabled": true,
    "offline_mode": "auto",
    "rule_fallback": true,
    "local_cache_ttl": 3600
  }
}
```

---

### 2.2 闭环设计：感知→决策→执行→反馈→校验→修正

#### 新增模块：`ExecutionVerifier`
```
backend/app/core/execution_verifier.py
```
**功能：**
- 执行结果校验
- 成功/失败确认
- 执行超时检测
- 执行状态持久化

#### 新增模块：`RetryHandler`
```
backend/app/core/retry_handler.py
```
**功能：**
- 重试策略（指数退避、固定间隔）
- 重试次数限制
- 失败告警
- 回滚机制

#### 扩展模型：`ExecutionRecord`
```
backend/app/models/execution_record.py
```
**字段：**
- id
- session_id
- iteration
- action
- action_input
- status (pending/executing/success/failed/rolled_back)
- result
- error
- verified_at
- retry_count
- created_at
- updated_at

#### 修改：`AgentLoop.execute()`
集成闭环流程：
```
THINK → PROPOSE → (HUMAN APPROVAL) → EXECUTE → VERIFY → (RETRY/ROLLBACK) → OBSERVE → REFLECT
```

---

### 2.3 LLM 提案-人审批机制强化

#### 修改：`HumanFeedbackService`
新增反馈类型：
```python
class FeedbackType(Enum):
    PROPOSAL_APPROVED = "proposal_approved"  # 提案通过
    PROPOSAL_REJECTED = "proposal_rejected"  # 提案拒绝
    PROPOSAL_MODIFIED = "proposal_modified"  # 提案修改
    EXECUTION_TERMINATION = "execution_termination"
    CONTINUE_EXECUTION = "continue_execution"
    TOOL_CALL_SUGGESTION = "tool_call_suggestion"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    STRATEGY_MODIFICATION = "strategy_modification"
```

#### 新增模块：`ProposalManager`
```
backend/app/core/proposal_manager.py
```
**功能：**
- 提案生成（LLM 输出结构化提案）
- 提案审核界面数据准备
- 提案版本管理
- 提案状态追踪

#### 新增模型：`Proposal`
```
backend/app/models/proposal.py
```
**字段：**
- id
- session_id
- iteration
- thought
- action
- action_input
- status (pending/approved/rejected/modified/executed)
- reviewer_id
- review_comment
- created_at
- reviewed_at

#### 前端改造：
新增提案审核界面组件：
```
frontend/src/components/gen-ui/ProposalReviewer.vue
```

---

### 2.4 幻觉防护：RAG 验证 + 不确定禁止执行 + 决策留痕

#### 新增模块：`HallucinationGuard`
```
backend/app/core/hallucination_guard.py
```
**功能：**
- RAG 验证检查（决策前检索验证）
- 不确定性检测（置信度评分）
- 不确定决策拦截
- 决策留痕记录

#### 扩展模型：`DecisionTrace`
```
backend/app/models/decision_trace.py
```
**字段：**
- id
- session_id
- iteration
- thought
- action
- rag_verified (true/false)
- confidence_score (0-1)
- sources (检索来源)
- is_allowed (true/false)
- created_at

#### 修改：`PromptEngine`
新增安全提示词：
```
安全原则：
1. 不确定的事情绝对不要执行
2. 所有事实性内容必须通过 RAG 验证
3. 如果没有足够信息，明确告知用户
```

---

### 2.5 工程化能力：协议对接 + 脏数据处理 + 异常检测 + 设备适配

#### 新增模块：`ProtocolAdapter`
```
backend/app/core/protocol_adapter.py
```
**功能：**
- REST API 协议适配
- MQTT 协议适配
- Modbus 协议适配（工业场景）
- 协议版本管理

#### 新增模块：`DataCleaner`
```
backend/app/core/data_cleaner.py
```
**功能：**
- 数据格式校验
- 脏数据检测
- 数据清洗规则
- 数据质量报告

#### 新增模块：`AnomalyDetector`
```
backend/app/core/anomaly_detector.py
```
**功能：**
- 异常行为检测
- 阈值告警
- 异常模式学习
- 实时告警通知

#### 新增模块：`DeviceAdapter`
```
backend/app/core/device_adapter.py
```
**功能：**
- 设备注册管理
- 设备状态监控
- 设备指令封装
- 设备适配层

---

### 2.6 安全机制：操作分级权限 + 高危操作二次确认

#### 扩展模型：`OperationPermission`
```
backend/app/models/operation_permission.py
```
**字段：**
- id
- operation_name
- risk_level (low/medium/high/critical)
- required_role
- requires_second_approval
- description

#### 新增模块：`RiskAssessor`
```
backend/app/core/risk_assessor.py
```
**功能：**
- 操作风险评估
- 权限检查
- 二次确认触发
- 高危操作审计

#### 扩展审计日志：`AuditLog`
新增字段：
```python
risk_level = Column(String(20), nullable=True)
requires_second_approval = Column(Boolean, default=False)
second_approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
approved_at = Column(DateTime, nullable=True)
```

---

## 三、实施步骤

### 阶段 1：基础架构搭建
1. 创建 `EdgeController` 和 `RuleEngine`
2. 创建 `ExecutionRecord` 模型
3. 创建 `DecisionTrace` 模型
4. 创建 `Proposal` 模型
5. 扩展 `OperationPermission` 模型

### 阶段 2：闭环系统实现
1. 实现 `ExecutionVerifier`
2. 实现 `RetryHandler`
3. 集成到 `AgentLoop`
4. 添加执行状态持久化

### 阶段 3：提案-审批机制
1. 增强 `HumanFeedbackService`
2. 实现 `ProposalManager`
3. 前端添加提案审核界面
4. 集成到 `AgentLoop` 流程

### 阶段 4：幻觉防护
1. 实现 `HallucinationGuard`
2. 集成 RAG 验证
3. 添加不确定性检测
4. 决策留痕记录

### 阶段 5：工程化能力
1. 实现 `ProtocolAdapter`
2. 实现 `DataCleaner`
3. 实现 `AnomalyDetector`
4. 实现 `DeviceAdapter`

### 阶段 6：安全机制
1. 实现 `RiskAssessor`
2. 配置操作分级权限
3. 实现二次确认流程
4. 增强审计日志

### 阶段 7：测试与优化
1. 单元测试
2. 集成测试
3. 压力测试
4. 安全审计

---

## 四、文件清单

### 新增文件
```
backend/app/core/
├── edge_controller.py          # 边缘控制器
├── rule_engine.py              # 规则引擎
├── execution_verifier.py       # 执行验证器
├── retry_handler.py            # 重试处理器
├── proposal_manager.py         # 提案管理器
├── hallucination_guard.py      # 幻觉防护
├── protocol_adapter.py         # 协议适配器
├── data_cleaner.py             # 数据清洗器
├── anomaly_detector.py         # 异常检测器
├── device_adapter.py           # 设备适配器
└── risk_assessor.py            # 风险评估器

backend/app/models/
├── execution_record.py         # 执行记录
├── decision_trace.py           # 决策留痕
├── proposal.py                 # 提案
└── operation_permission.py     # 操作权限

frontend/src/components/gen-ui/
└── ProposalReviewer.vue        # 提案审核组件
```

### 修改文件
```
backend/app/agents/
├── agent_loop.py               # 集成新模块
└── types.py                    # 新增事件类型

backend/app/services/
└── human_feedback_service.py   # 增强反馈类型

backend/app/models/
└── audit_log.py                # 扩展字段

backend/app/core/
└── config.py                   # 新增配置项

config.json.example             # 新增配置示例
```

---

## 五、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 改造范围大，工期长 | 高 | 分阶段实施，每阶段可独立运行 |
| 性能下降（新增验证层） | 中 | 优化关键路径，异步非关键操作 |
| 兼容性问题 | 中 | 保持旧接口兼容，渐进式迁移 |
| 学习曲线陡峭 | 中 | 提供详细文档和示例 |

---

## 六、成功标准

1. ✅ 断网时自动切换到规则系统
2. ✅ 所有执行有确认、失败有重试/回滚
3. ✅ LLM 提案必须人审批后才能执行
4. ✅ 不确定决策被拦截，所有决策可追溯
5. ✅ 支持多种工业协议，脏数据自动清洗
6. ✅ 高危操作必须二次确认
7. ✅ 7x24 小时稳定运行，毫秒级响应
