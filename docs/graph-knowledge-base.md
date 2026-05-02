# 图结构知识库

## 原理

### 为什么需要图结构

传统向量知识库只有一层：文档→切片→嵌入→相似度搜索。能回答"这个文档讲了什么"，但无法回答结构性问题。

```
Chroma 向量库:
  文档 → chunk_1 → [0.12, -0.34, ...]
       → chunk_2 → [0.08,  0.67, ...]
       → chunk_3 → [-0.22, 0.41, ...]
  
  "用了 WorldView-3 数据集的还有谁？"
  → 向量相似度搜索 "WorldView-3" → 可能只找回白钰傅文档的一个片段
  → 无法精确追溯到"所有用了这个数据集的文档"
```

图结构在向量层之上增加**实体关系网络**：

```
  DOCUMENT: 白钰傅-全色多光谱融合
    ├─ CONTAINS → 方法: PANet
    ├─ CONTAINS → 数据集: WorldView-3
    └─ CONTAINS → 指标: PSNR=32.5

  DOCUMENT: 李四-遥感变化检测
    ├─ CONTAINS → 方法: Transformer
    └─ CONTAINS → 数据集: WorldView-3   ← 同数据集！

  "用了 WorldView-3 数据集的还有谁？"
  → 节点 WorldView-3 → 反向遍历 CONTAINS 边 → 白钰傅、李四 ✓
```

### 架构

```
文档上传
  │
  ├─ 向量摄入 (Chroma)        ← 语义搜索
  │
  └─ 实体提取 (LLM)           ← 新增
       │
       ├─ 实体消歧 (嵌入相似度)
       ├─ 写入图数据库 (SQLite + NetworkX)
       └─ 自动跨文档链接
       
用户提问
  │
  ├─ 问题分类 (QueryRouter)
  │
  ├─ "有哪些X"           → 图查询
  ├─ "A和B的关系"         → 图遍历
  └─ "讲什么的"           → 向量搜索 (兜底)
```

### 核心设计原则

1. **实体类型不预定义** — LLM 根据文档内容自主决定实体类型，论文/会议纪要/代码/笔记都适用
2. **跨文档自动链接** — 新文档的实体通过嵌入相似度自动匹配已有实体，织入关系网
3. **增量更新** — 检测文档内容 hash，仅变更时重新提取
4. **非致命降级** — 图提取失败不影响向量摄入和问答

## 示例

### 示例 1：学术论文

上传 `研三-白钰傅-全色-多光谱-高光谱融合-TGRS.md`，LLM 提取：

```json
{
  "entities": [
    {"type": "方法",   "name": "PANet",       "description": "全色-多光谱融合网络"},
    {"type": "方法",   "name": "FusionNet",   "description": "对比基线方法"},
    {"type": "数据集", "name": "WorldView-3",  "description": "高分辨率遥感卫星"},
    {"type": "指标",   "name": "PSNR=32.5",   "description": "峰值信噪比"},
    {"type": "概念",   "name": "全色锐化",     "description": "空间细节注入多光谱"},
    {"type": "期刊",   "name": "TGRS",         "description": "IEEE TGRS"}
  ],
  "relations": [
    {"source": "PANet", "target": "FusionNet",  "type": "对比"},
    {"source": "PANet", "target": "WorldView-3", "type": "使用"},
    {"source": "PSNR=32.5", "target": "PANet",  "type": "评估"}
  ]
}
```

图中自动建立：白钰傅文档 —(CONTAINS)→ PANet, WorldView-3, PSNR...

### 示例 2：会议纪要

上传 `2025-01-组会纪要.md`：

```json
{
  "entities": [
    {"type": "议题",   "name": "Q1实验方案"},
    {"type": "决策",   "name": "改用Transformer"},
    {"type": "负责人", "name": "张三"},
    {"type": "截止日期", "name": "2025-02-01"}
  ],
  "relations": [
    {"source": "张三", "target": "Q1实验方案", "type": "负责"},
    {"source": "改用Transformer", "target": "Q1实验方案", "type": "影响"}
  ]
}
```

同一套流程，不需要改任何代码。

### 示例 3：跨文档自动关联

已入库：
- 白钰傅文档 → 实体 `WorldView-3`
- 钟鑫涛文档 → 实体 `WorldView-3`

新上传：
- 李四文档 → LLM 提取到 `WorldView-3`

系统自动通过嵌入相似度匹配到已有节点，创建连接：

```
李四文档 ←SHARES_ENTITY→ 白钰傅文档 (共享 WorldView-3)
李四文档 ←SHARES_ENTITY→ 钟鑫涛文档 (共享 WorldView-3)
```

无需人工标注，自动织入关系网。

## 使用方式

### 启用/禁用

图搜索默认开启。可通过前端「模式设置」面板中的「图结构检索」开关控制。

也可以在配置中设置：
```json
// config.json
{
  "graph_search": {
    "enabled": true
  }
}
```

### 上传文件自动生效

上传任何文档到知识库，系统自动：
1. 向量切片 + 嵌入 (Chroma)
2. 实体提取 + 图写入 (GraphStore)

无需额外操作。日志中看到 `Graph layer: xxx.md → new (N entities, M relations)` 表示成功。

### 查询类型

| 问题类型 | 示例 | 检索方式 |
|---------|------|---------|
| 实体列表 | "组里有哪些方法"、"用了什么数据集" | 图查询 |
| 关系查询 | "PANet 和 WorldView-3 什么关系" | 图遍历 |
| 关联文档 | "用了同一数据集的有哪些论文" | 图遍历 |
| 语义理解 | "这篇文章讲了什么" | 向量搜索(兜底) |

### 查看图状态

调用 API 获取图统计：
```bash
GET /api/graph/stats
```

返回节点数、边数、文档数、实体类型分布。

### 分析

查看社区检测结果和枢纽节点：
```bash
GET /api/graph/communities    # 社区检测结果
GET /api/graph/stats          # 图统计信息
```

## 技术实现

### 存储

- **SQLite**: 节点表 + 边表 + doc_versions (增量检测) + FTS5 (全文搜索)
- **NetworkX**: 内存图，BFS 遍历、最短路径、社区检测
- **嵌入**: 复用现有 EmbeddingService (BAAI/bge-small-zh-v1.5)，实体名嵌入用于消歧

### 文件清单

| 文件 | 职责 |
|------|------|
| `app/services/graph_store.py` | 图存储 (SQLite + NetworkX) |
| `app/services/entity_extractor.py` | 实体提取 (LLM 驱动，零硬编码类型) |
| `app/services/graph_search.py` | 图检索 (实体查找 + BFS + 混合搜索) |
| `app/services/query_router.py` | 问题分类 + 路由 |
| `app/services/graph_analysis.py` | 图分析 (社区检测、枢纽节点、路径) |
| `app/services/ingest.py` | 摄入集成 (文档上传后自动触发提取) |
| `app/services/qa/stream_answer.py` | QA 集成 (检索前可选图搜索) |
