# Tasks

- [x] Task 1: 优化实体提取提示词（entity_extractor.py）
  - [x] SubTask 1.1: 修改 ENTITY_EXTRACTION_PROMPT，区分事实型信息和需详细解释的信息
  - [x] SubTask 1.2: 为实体增加 properties 结构化属性提示（人物/组织/文档类型的典型属性示例）
  - [x] SubTask 1.3: 添加 EXTRACTOR_VERSION = "1.1.0" 常量

- [x] Task 2: 新增 graph_store.py 辅助方法
  - [x] SubTask 2.1: 实现 get_entities_by_document(self, filename) 方法，返回含 properties 的实体列表
  - [x] SubTask 2.2: 验证现有 find_path 方法返回格式与优化计划一致（如不一致则适配）

- [x] Task 3: 新增 format_route_result 函数（query_router.py）
  - [x] SubTask 3.1: 实现 format_route_result(question, graph_store, router_result) 函数
  - [x] SubTask 3.2: 实现实体去重逻辑（seen_entity_names）
  - [x] SubTask 3.3: 实现路径去重逻辑（seen_path_keys，双向去重）
  - [x] SubTask 3.4: 实现 extract_entities_from_question 辅助函数

- [x] Task 4: 新建 graph_retrieval_judge.py（LLM 逻辑判断模块）
  - [x] SubTask 4.1: 实现 judge_graph_sufficiency(question, route_result) 主函数
  - [x] SubTask 4.2: 实现 _rule_based_judge(question, route_result) 规则 fallback
  - [x] SubTask 4.3: 设计并实现 JUDGE_SYSTEM_PROMPT 和 JUDGE_USER_PROMPT_TEMPLATE
  - [x] SubTask 4.4: 实现 LLM 调用和 JSON 解析逻辑
  - [x] SubTask 4.5: 确保异常处理和 fallback 机制

- [x] Task 5: 增强 parent_retriever.py（支持线索传递）
  - [x] SubTask 5.1: 实现 search_in_documents(self, query, target_documents) 方法
  - [x] SubTask 5.2: 实现 enhance_query(self, original_query, suggestions) 方法
  - [x] SubTask 5.3: 实现 rerank_with_focus(self, results, focus_entities) 方法
  - [x] SubTask 5.4: 实现 _deduplicate_results(self, results) 方法
  - [x] SubTask 5.5: 实现 retrieve_with_clues(self, original_query, suggestions) 主方法

- [x] Task 6: 修改 stream_answer.py 主流程
  - [x] SubTask 6.1: 在顶部导入区增加新的导入语句
  - [x] SubTask 6.2: 修改图检索逻辑，调用 format_route_result 格式化图结果
  - [x] SubTask 6.3: 增加 LLM 逻辑判断分支（sufficient=true / sufficient=false）
  - [x] SubTask 6.4: 实现 _format_parent_documents 辅助函数
  - [x] SubTask 6.5: 修改 Context 构建逻辑，合并图上下文 + 父子检索结果 + focus_prompt
  - [x] SubTask 6.6: 移除 _fetch_graph_document_text 中的 chunk 获取逻辑

- [x] Task 7: 新增配置项（config.py）
  - [x] SubTask 7.1: 在 graph_search 配置中增加 enable_llm_judge 和 fallback_to_parent
  - [x] SubTask 7.2: 在 parent_document_retrieval 配置中确认 parent_max_count 参数可用

- [x] Task 8: 图自动更新机制
  - [x] SubTask 8.1: 在 graph_store.py 中增加提取器版本追踪逻辑
  - [x] SubTask 8.2: 实现自动检查触发（系统启动时检查版本差异）
  - [x] SubTask 8.3: 实现自动更新逻辑（版本变更时重新提取实体和关系）

- [x] Task 9: 功能验证和测试
  - [x] SubTask 9.1: 验证事实查询场景（图足够时只用图检索）
  - [x] SubTask 9.2: 验证详细信息查询场景（图不够时使用父子检索补充）
  - [x] SubTask 9.3: 验证 LLM 判断失败时的规则 fallback
  - [x] SubTask 9.4: 验证线索传递的完整利用（4个suggestion字段在检索和答案生成阶段均生效）
  - [x] SubTask 9.5: 验证图自动更新机制

# Task Dependencies
- [Task 2] depends on [Task 1] (get_entities_by_document 需要新的 properties 格式)
- [Task 3] depends on [Task 2] (format_route_result 调用 get_entities_by_document 和 find_path)
- [Task 4] depends on [Task 3] (judge_graph_sufficiency 接收 format_route_result 的输出)
- [Task 5] is independent of [Task 4] (可以并行开发)
- [Task 6] depends on [Task 3, Task 4, Task 5] (主流程集成需要所有模块就绪)
- [Task 7] is independent (可以并行开发)
- [Task 8] depends on [Task 1] (需要 EXTRACTOR_VERSION)
- [Task 9] depends on [Task 6, Task 7, Task 8] (验证需要所有功能完成)
