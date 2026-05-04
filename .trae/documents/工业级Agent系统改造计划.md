# 工业级 Agent 系统改造计划

## 现状分析

当前系统是一个基于 ReAct 模式的 AI Agent,主要面向实验室场景的问答和工具调用。现有架构包含:
- ReAct Agent 循环引擎(思考→行动→观察)
- 工具注册和执行系统(Action Engine)
- 基础的错误处理和重试机制
- 简单的时间限制配置
- 基础的权限和用户管理

**问题诊断:**
1. **没有降级机制** - 当 AI 服务不可用时,系统完全崩溃,无规则系统备选
2. **没有闭环校验** - 工具执行后只返回成功/失败,没有执行确认、回滚机制
3. **大模型直接执行** - LLM 的决策直接执行,无人工审核环节
4. **幻觉风险未控制** - 没有 RAG 验证机制,不确定情况下仍会执行
5. **异常处理简单** - 只有基础的重试,没有脏数据清洗、异常检测
6. **安全机制薄弱** - 权限模型存在但未分级,无高危操作二次确认

---

## 改造方案

### 阶段一:边缘控制 + 降级机制

**目标:** 控制必须在边缘,断网也能降级运行

#### 1.1 多层降级架构
```
优先级层级:
L1 - 规则引擎(Rule Engine)     ← 断网/超时时的最终防线
L2 - 本地缓存决策              ← 短时网络波动
L3 - 云端大模型决策            ← 正常运行时
```

**实现:**
- 新建 `backend/app/rule_engine/` 目录
  - `rule_parser.py` - 解析预定义的 JSON/YAML 规则文件
  - `rule_executor.py` - 执行规则,不依赖 LLM
  - `rule_fallback.py` - 降级控制器,监控 LLM 可用性并自动切换
- 新建 `config/rules/` 目录存放规则文件
  - `default_rules.yaml` - 默认规则集
  - `emergency_rules.yaml` - 紧急规则集(更保守)
- 修改 `backend/app/core/config.py`:
  - 添加 `fallback_mode` 配置项
  - 添加规则引擎超时阈值(毫秒级)
  - 添加健康检查间隔

#### 1.2 毫秒级响应保证
- 在 `config.json` 的 `timeouts` 中添加:
  ```json
  "response_requirements": {
    "rule_engine_max_ms": 50,
    "llm_timeout_ms": 5000,
    "fallback_trigger_ms": 5000
  }
  ```
- 规则引擎必须在 50ms 内返回结果
- LLM 超时后自动切换到规则引擎

#### 1.3 断网检测和自动切换
- 新建 `backend/app/infrastructure/health_monitor.py`:
  - 持续检测 LLM 服务可用性(心跳检测)
  - 检测到故障后自动切换至规则引擎
  - 记录切换日志(审计用)

---

### 阶段二:闭环设计(感知→决策→执行→反馈→校验→修正)

**目标:** 这是生死线!每个指令必须有确认、失败有处理

#### 2.1 闭环控制器
- 新建 `backend/app/core/closed_loop_controller.py`:
  ```
  状态机:
  PENDING → EXECUTING → CONFIRMED → VALIDATED → COMPLETED
                ↓              ↓
            FAILED        INVALID
                ↓              ↓
           RETRY/ROLLBACK  CORRECT → RE-EXECUTE
  ```

**核心组件:**
- `CommandIssuer` - 指令发送器,记录指令 ID、时间戳、参数
- `ExecutionWatcher` - 执行监控器,轮询确认执行状态
- `ResultValidator` - 结果校验器,验证执行结果是否符合预期
- `RollbackManager` - 回滚管理器,失败时执行回滚
- `AlertSystem` - 报警系统,重试多次失败后报警

#### 2.2 指令确认机制
- 修改 `backend/app/agents/action_engine.py`:
  - 每次工具执行后必须返回确认信息
  - 添加 `require_confirmation` 标志
  - 执行结果必须包含:执行状态、实际影响、可验证结果

#### 2.3 重试和回滚策略
- 新建 `backend/app/core/retry_rollback.py`:
  - 可配置重试次数(默认 3 次)
  - 指数退避重试间隔
  - 回滚脚本注册表(每个操作对应一个回滚操作)
  - 回滚失败触发报警

#### 2.4 闭环数据库记录
- 新建 `backend/app/models/closed_loop_log.py`:
  - 记录每次指令的完整生命周期
  - 字段:指令 ID、状态变化时间线、执行结果、校验结果、回滚记录

---

### 阶段三:大模型决策 + 人工审核(人机协同)

**目标:** 大模型只负责提案,人负责审核后才执行

#### 3.1 提案-审核-执行 工作流
```
用户请求 → LLM 分析 → 生成提案(Proposal) → 前端展示提案 → 人工审核 → 
  ├─ 通过 → 执行 → 反馈结果
  └─ 拒绝 → 返回拒绝原因 → 重新分析或结束
```

**实现:**
- 新建 `backend/app/models/proposal.py`:
  - Proposal 模型:包含建议操作、预期结果、风险等级、置信度
- 新建 `backend/app/api/proposals.py`:
  - POST `/proposals/create` - 创建提案
  - GET `/proposals/list` - 列出待审核提案
  - POST `/proposals/{id}/approve` - 审核通过
  - POST `/proposals/{id}/reject` - 审核拒绝
- 修改 `frontend/src/components/gen-ui/`:
  - 新建 `ProposalReview.vue` - 提案审核组件
  - 修改 `ChatView.vue` - 在执行前展示提案并等待确认

#### 3.2 风险分级
- 在提案中添加风险等级:
  - **LOW** - 只读操作,自动执行(如查询天气)
  - **MEDIUM** - 需要确认(如修改配置)
  - **HIGH** - 必须人工审核(如删除数据)
  - **CRITICAL** - 必须二次确认 + 高级权限

#### 3.3 自动执行白名单
- 新建 `config/auto_execute_whitelist.yaml`:
  - 定义哪些操作可以自动执行(低风险、只读)
  - 其他所有操作必须走审核流程

---

### 阶段四:幻觉防护(验证 + 留痕 + 禁止不确定执行)

**目标:** 幻觉不是优化问题,是事故源

#### 4.1 RAG 验证层
- 新建 `backend/app/agents/hallucination_guard.py`:
  ```
  LLM 输出 → RAG 知识库验证 → 
    ├─ 置信度高 → 继续执行
    ├─ 置信度中 → 标记为需要人工确认
    └─ 置信度低 → 直接拒绝执行
  ```

**实现:**
- 每个工具调用前,先用 RAG 验证:
  - 查询知识库确认操作是否合理
  - 计算置信度分数
  - 低置信度直接阻断
- 修改 `backend/app/agents/action_engine.py`:
  - 在执行前插入 `HallucinationGuard` 检查
  - 添加 `confidence_threshold` 配置

#### 4.2 不确定性检测
- 新建 `backend/app/agents/uncertainty_detector.py`:
  - 检测 LLM 输出中的不确定词汇("可能"、"也许"、"大概")
  - 检测到不确定性后:
    - 不执行操作
    - 返回给用户说明原因
    - 记录日志

#### 4.3 决策留痕(Audit Trail)
- 新建 `backend/app/models/audit_trail.py`:
  - 记录每次决策的完整信息:
    - 决策时间、决策者(LLM/规则引擎/人工)
    - 输入参数、输出结果、置信度
    - 审核人员、审核时间
    - 执行状态
- 新建 `backend/app/api/audit.py`:
  - GET `/audit/logs` - 查询审计日志
  - 支持按时间、操作类型、决策者筛选

#### 4.4 不确定性 = 禁止执行
- 修改 `backend/app/agents/react_agent.py`:
  - 在 `execute()` 方法中插入不确定性检查
  - 如果检测到不确定性,直接返回错误而不是继续执行
  - 添加明确的日志记录

---

### 阶段五:工程化(协议对接 + 脏数据 + 异常检测 + 设备适配)

**目标:** 解决真正的难点——工程问题

#### 5.1 协议对接层
- 新建 `backend/app/protocols/` 目录:
  - `base_protocol.py` - 协议基类
  - `modbus_protocol.py` - Modbus 协议适配器
  - `mqtt_protocol.py` - MQTT 协议适配器
  - `http_protocol.py` - HTTP REST 协议适配器
  - `serial_protocol.py` - 串口协议适配器
- 每个协议适配器包含:
  - 连接管理(连接池、心跳)
  - 数据格式转换
  - 错误处理
  - 超时控制

#### 5.2 脏数据清洗
- 新建 `backend/app/data/data_cleaner.py`:
  - 输入验证(类型、范围、格式)
  - 异常值检测和过滤
  - 数据标准化
  - 缺失值处理策略

#### 5.3 异常检测
- 新建 `backend/app/data/anomaly_detector.py`:
  - 统计异常检测(均值、标准差)
  - 规则异常检测(超出合理范围)
  - 时序异常检测(突变检测)
  - 异常报警和记录

#### 5.4 设备适配层
- 新建 `backend/app/devices/` 目录:
  - `device_registry.py` - 设备注册表
  - `device_adapter.py` - 设备适配器基类
  - `device_health.py` - 设备健康监控
- 每个设备适配器包含:
  - 设备连接管理
  - 数据读取/写入
  - 状态监控
  - 故障诊断

---

### 阶段六:安全机制(权限分级 + 高危操作二次确认)

**目标:** 操作必须分权限,高危操作必须二次确认

#### 6.1 权限分级系统
- 修改 `backend/app/models/permission.py`:
  ```
  权限等级:
  - LEVEL_1(只读) - 查看数据、查询状态
  - LEVEL_2(操作) - 执行常规操作、修改配置
  - LEVEL_3(管理) - 删除数据、修改权限
  - LEVEL_4(超级) - 系统级操作、紧急处理
  ```

#### 6.2 操作权限映射
- 新建 `config/operation_permissions.yaml`:
  - 定义每个操作需要的最低权限等级
  - 示例:
    ```yaml
    operations:
      query_weather: LEVEL_1
      modify_config: LEVEL_2
      delete_data: LEVEL_3
      emergency_shutdown: LEVEL_4
    ```

#### 6.3 高危操作二次确认
- 新建 `backend/app/security/high_risk_confirm.py`:
  - 识别高危操作(删除、修改关键配置、紧急操作)
  - 要求二次确认:
    - 第一次确认:操作者本人
    - 第二次确认:更高权限人员或延迟确认
  - 记录确认日志

#### 6.4 前端安全组件
- 新建 `frontend/src/components/security/`:
  - `HighRiskConfirm.vue` - 高危操作确认对话框
  - `PermissionGuard.vue` - 权限守卫组件
  - `AuditLogViewer.vue` - 审计日志查看器

---

### 阶段七:7×24 小时稳定性保障

**目标:** 系统稳定运行,不崩溃

#### 7.1 健康检查和自愈
- 新建 `backend/app/infrastructure/health_check.py`:
  - 定期检查各组件状态(LLM、数据库、设备连接)
  - 检测到故障自动重启或切换
  - 发送健康状态报告

#### 7.2 资源监控
- 新建 `backend/app/infrastructure/resource_monitor.py`:
  - 监控 CPU、内存、磁盘使用
  - 监控数据库连接池状态
  - 达到阈值时自动清理或报警

#### 7.3 优雅降级和恢复
- 修改现有降级机制:
  - 负载过高时自动降低 LLM 调用频率
  - 内存不足时清理缓存
  - 网络恢复后自动恢复至正常运行模式

#### 7.4 日志和监控集成
- 统一日志格式:
  - 结构化日志(JSON 格式)
  - 包含:时间戳、级别、模块、操作 ID、用户 ID
- 集成监控指标:
  - 响应时间
  - 错误率
  - 降级切换次数
  - 人工审核通过率

---

## 实施优先级

### P0(立即实施 - 安全底线)
1. 降级机制(阶段一)
2. 闭环设计(阶段二)
3. 幻觉防护(阶段四)

### P1(短期实施 - 核心功能)
4. 人机协同审核(阶段三)
5. 安全机制(阶段六)

### P2(中期实施 - 工程化)
6. 协议对接和设备适配(阶段五)

### P3(持续优化 - 稳定性)
7. 7×24 稳定性保障(阶段七)

---

## 配置变更

### config.json 新增配置项
```json
{
  "industrial_mode": {
    "enabled": true,
    "fallback": {
      "enabled": true,
      "trigger_timeout_ms": 5000,
      "health_check_interval_s": 30
    },
    "closed_loop": {
      "enabled": true,
      "max_retries": 3,
      "retry_backoff_ms": 1000,
      "require_confirmation": true
    },
    "hallucination_guard": {
      "enabled": true,
      "confidence_threshold": 0.7,
      "require_rag_validation": true
    },
    "human_in_the_loop": {
      "enabled": true,
      "auto_execute_whitelist": ["query_weather", "search_arxiv"],
      "require_review_for": ["HIGH", "CRITICAL"]
    },
    "security": {
      "permission_levels": 4,
      "high_risk_double_confirm": true,
      "audit_trail_enabled": true
    },
    "stability": {
      "health_check_enabled": true,
      "resource_monitor_enabled": true,
      "auto_recovery_enabled": true
    }
  }
}
```

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 降级机制切换延迟 | 响应变慢 | 毫秒级规则引擎,预加载规则 |
| 人工审核流程增加延迟 | 用户体验 | 低风险操作自动执行白名单 |
| RAG 验证增加开销 | 响应时间 | 异步验证,缓存常见查询结果 |
| 数据库压力增加 | 性能 | 优化索引,异步写入审计日志 |
| 协议适配复杂性 | 开发成本 | 先支持核心协议,逐步扩展 |

---

## 预期效果

改造完成后,系统将具备以下工业级特性:
1. **高可用** - 断网/故障时自动降级,7×24 小时运行
2. **可追溯** - 每个决策和执行都有完整审计日志
3. **安全可控** - 人机协同,幻觉防护,权限分级
4. **稳定可靠** - 闭环校验,异常检测,自愈能力
5. **工程化** - 协议对接,脏数据处理,设备适配
