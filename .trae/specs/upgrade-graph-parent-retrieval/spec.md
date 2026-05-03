# 图检索和父子检索架构升级 Spec

## Why
当前系统在图检索和向量检索的协同上存在设计缺陷：图检索结果不够时没有智能判断和 fallback 机制，图检索内部混入了不必要的文档 chunk 获取逻辑，且父子检索无法利用图检索提供的线索来优化检索方向。需要实现「图检索 → LLM 逻辑判断 → 父子检索（带线索）」的分层架构，让检索流程更智能、更精准。

## What Changes
- 优化实体提取提示词 `ENTITY_EXTRACTION_PROMPT`，区分事实型信息和需详细解释的信息，增加 properties 结构化属性
- 新增 `format_route_result` 函数，将原始图检索结果格式化为 LLM 友好的结构（含实体去重和路径去重）
- 新增 `graph_store.py` 辅助方法：`get_entities_by_document`（按文档获取实体含 properties）
- 新建 `graph_retrieval_judge.py`，实现 LLM 逻辑判断模块（含规则 fallback）
- 增强 `parent_retriever.py`，新增 `retrieve_with_clues`、`search_in_documents`、`enhance_query`、`rerank_with_focus`、`_deduplicate_results` 方法
- 修改 `stream_answer.py` 主流程：图检索后调用 LLM 判断，根据判断结果选择只用图或图+父子检索
- 新增 `_format_parent_documents` 辅助函数，构建 focus_prompt 利用 focus_entities 和 search_angle
- 移除 `_fetch_graph_document_text` 中的 chunk 获取逻辑（图检索不再负责获取文档 chunks）
- 新增图自动更新机制：提取器版本号追踪 + 自动重建
- 新增配置项 `graph_search.enable_llm_judge` 和 `graph_search.fallback_to_parent`

## Impact
- Affected specs: 图检索流程、父子检索流程、QA 主流程
- Affected code:
  - `backend/app/services/entity_extractor.py` — 修改 ENTITY_EXTRACTION_PROMPT
  - `backend/app/services/graph_store.py` — 新增 get_entities_by_document 方法
  - `backend/app/services/query_router.py` — 新增 format_route_result 函数
  - `backend/app/services/graph_retrieval_judge.py` — 新建文件
  - `backend/app/services/parent_retriever.py` — 新增 5 个方法
  - `backend/app/services/qa/stream_answer.py` — 修改主流程和新增辅助函数
  - `backend/app/core/config.py` — 新增配置项

## ADDED Requirements

### Requirement: LLM 逻辑判断图检索充分性
系统 SHALL 在图检索完成后，使用 LLM 判断图检索结果是否足够回答用户问题。判断标准为逻辑链路完整性（非数量），即回答问题所需的关键信息点是否被图检索结果覆盖。

#### Scenario: 图检索逻辑链路完整
- **WHEN** 用户提问"张三在哪个公司工作？"且图检索找到了"张三-工作单位-宁波拓普"的完整关系路径
- **THEN** LLM 判断 sufficient=true，系统仅使用图检索结果生成回答

#### Scenario: 图检索逻辑链路不完整
- **WHEN** 用户提问"详细介绍一下张三的背景？"且图检索只找到了张三实体，缺少工作经历、教育背景等详细信息
- **THEN** LLM 判断 sufficient=false，系统提取线索并使用父子检索补充信息

#### Scenario: LLM 判断调用失败
- **WHEN** LLM 判断模块调用超时或失败
- **THEN** 系统使用规则 fallback 进行判断，确保流程不中断

### Requirement: 父子检索线索传递
系统 SHALL 在图检索不充分时，将 LLM 生成的线索（target_documents、focus_entities、search_angle、query_hint）传递给父子检索模块，用于优化检索方向和结果质量。

#### Scenario: 使用 target_documents 限制检索范围
- **WHEN** suggestions 中包含 target_documents
- **THEN** 父子检索优先在指定文档范围内搜索

#### Scenario: 使用 focus_entities 重排序
- **WHEN** suggestions 中包含 focus_entities
- **THEN** 检索结果中提到 focus_entities 的文档优先排列

#### Scenario: 使用 query_hint 优化查询
- **WHEN** suggestions 中包含 query_hint
- **THEN** 父子检索使用优化后的查询词替代或补充原查询

#### Scenario: 使用 search_angle 和 focus_entities 优化答案生成
- **WHEN** suggestions 中包含 search_angle 或 focus_entities
- **THEN** 系统在构建最终 prompt 时加入 focus_prompt，引导 LLM 侧重点回答

### Requirement: 图检索结果格式化
系统 SHALL 将原始图检索结果格式化为包含 route、related_entities（含 properties）、merged_documents、paths 的统一结构，并确保实体和路径去重。

#### Scenario: 格式化图检索结果
- **WHEN** query_router 返回原始图检索结果
- **THEN** format_route_result 函数将其转换为统一格式，包含从图中获取的实体 properties 和关系路径

### Requirement: 实体提取优化
系统 SHALL 优化实体提取提示词，区分事实型信息（存入图）和需详细解释的信息（留给父子检索），并为实体增加结构化 properties 属性。

#### Scenario: 提取人物实体含 properties
- **WHEN** 文档中包含"张三，软件工程师，清华大学毕业"
- **THEN** 实体提取结果包含 properties: {"职位": "软件工程师", "学校": "清华大学"}

### Requirement: 图自动更新机制
系统 SHALL 追踪实体提取器版本号，当版本变更或文档内容变更时，自动重新提取实体和关系并更新图结构。

#### Scenario: 提取器版本升级后自动更新
- **WHEN** entity_extractor.py 中的 EXTRACTOR_VERSION 从 "1.0.0" 变更为 "1.1.0"
- **THEN** 系统在下次启动或检索到相关文档时，自动重新提取该文档的实体和关系

## MODIFIED Requirements

### Requirement: 图检索流程
原流程：图检索 → 获取文档 chunks → 合并到 context
新流程：图检索 → format_route_result → LLM 逻辑判断 → sufficient=true 只用图 / sufficient=false 图+父子检索（带线索）

### Requirement: 父子检索
原功能：仅支持全库检索
新功能：支持线索传递（target_documents 限制范围、focus_entities 重排序、query_hint 优化查询、search_angle 优化答案生成），两阶段检索（限制范围 → 全库补充）

### Requirement: stream_answer 主流程
原逻辑：图检索结果直接获取文档 chunks 并合并到 context
新逻辑：图检索结果经 LLM 判断后，决定只用图或图+父子检索，并利用线索优化检索和答案生成

## REMOVED Requirements

### Requirement: 图检索获取文档 chunks
**Reason**: 图检索定位为结构化信息源，不负责获取详细文档内容，详细内容交给父子检索
**Migration**: 原 `_fetch_graph_document_text` 函数的 chunk 获取逻辑将被移除，由父子检索的 `retrieve_with_clues` 替代
