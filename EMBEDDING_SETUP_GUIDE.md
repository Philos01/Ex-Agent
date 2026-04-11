
# 嵌入模型本地部署指南

本指南介绍如何将嵌入模型从云端调用迁移到本地部署方案。

## 目录
1. [推荐的本地嵌入模型](#推荐的本地嵌入模型)
2. [代码架构说明](#代码架构说明)
3. [使用方法](#使用方法)
4. [API 接口说明](#api-接口说明)
5. [常见问题](#常见问题)

---

## 推荐的本地嵌入模型

以下是基于 Hugging Face 生态系统的高质量嵌入模型推荐：

### 1. BAAI/bge-small-zh-v1.5 ⭐ 推荐
- **描述**: 中文小型嵌入模型，适合普通硬件，语义理解能力良好
- **维度**: 512
- **语言**: 中文
- **优势**:
  - 模型体积小，加载速度快
  - 在中文任务上表现优秀
  - 内存占用低，适合普通 PC
- **硬件要求**: 4GB 以上内存即可

### 2. BAAI/bge-base-zh-v1.5
- **描述**: 中文基础嵌入模型，性能更好，需要更多内存
- **维度**: 768
- **语言**: 中文
- **优势**: 语义理解能力更强
- **硬件要求**: 8GB 以上内存

### 3. shibing624/text2vec-base-chinese
- **描述**: 轻量级中文文本嵌入模型
- **维度**: 768
- **语言**: 中文

### 4. all-MiniLM-L6-v2
- **描述**: 通用小型多语言嵌入模型，速度快
- **维度**: 384
- **语言**: 多语言

### 5. m3e-base
- **描述**: M3E中文嵌入模型，在多项任务上表现优秀
- **维度**: 768
- **语言**: 中文

---

## 代码架构说明

### 文件结构
```
backend/app/services/
├── embedding.py          # 统一的嵌入模型服务
└── vector_store.py       # 向量库服务（已更新）
```

### 核心类

#### 1. BaseEmbeddingProvider (抽象基类)
定义了嵌入模型提供者的统一接口：
- `embed_texts(texts: List[str]) -&gt; List[List[float]]`: 对文本列表进行嵌入
- `get_embedding_dimension() -&gt; int`: 获取嵌入向量维度

#### 2. LocalEmbeddingProvider (本地模型)
使用 Sentence-Transformers 加载和运行本地模型。

#### 3. OpenAIEmbeddingProvider (云端API)
调用 OpenAI API 进行嵌入，保持向后兼容。

#### 4. EmbeddingService (统一服务)
单例模式，支持在本地和云端模式之间无缝切换。

---

## 使用方法

### 1. 配置文件说明

在 `config.json` 中新增以下配置项：

```json
{
  "embedding_mode": "local",
  "local_embedding_model": "BAAI/bge-small-zh-v1.5",
  "local_model_cache_dir": ""
}
```

**配置项说明**:
- `embedding_mode`: 嵌入模式，可选值为 `"local"` 或 `"openai"`
- `local_embedding_model`: 本地模型名称（Hugging Face 模型 ID）
- `local_model_cache_dir`: 模型缓存目录（可选，留空使用默认目录）

### 2. Python 代码使用示例

#### 初始化嵌入服务
```python
from app.services.embedding import EmbeddingService
from app.core.config import load_config

# 加载配置
cfg = load_config()

# 初始化服务（自动根据配置选择模式）
EmbeddingService.initialize(mode=cfg["embedding_mode"], config=cfg)
```

#### 文本嵌入
```python
# 对单个文本进行嵌入
text = "这是一段测试文本"
embeddings = EmbeddingService.embed_texts([text])
print(f"嵌入向量维度: {len(embeddings[0])}")

# 对多个文本进行嵌入
texts = ["文本1", "文本2", "文本3"]
embeddings = EmbeddingService.embed_texts(texts)
print(f"生成了 {len(embeddings)} 个嵌入向量")
```

#### 获取当前模式和维度
```python
# 获取当前模式
mode = EmbeddingService.get_current_mode()
print(f"当前模式: {mode}")

# 获取嵌入维度
dim = EmbeddingService.get_embedding_dimension()
print(f"嵌入维度: {dim}")
```

#### 切换模式
```python
# 切换到本地模式（需要重启服务或重新初始化）
cfg["embedding_mode"] = "local"
cfg["local_embedding_model"] = "BAAI/bge-small-zh-v1.5"
save_config(cfg)

# 注意：切换模式后建议重置向量库，因为维度可能不同
from app.services.vector_store import reset_collection
reset_collection()
```

### 3. 切换嵌入模型的注意事项

⚠️ **重要**: 切换嵌入模型或模式时，向量维度可能会发生变化，需要：
1. 重置向量库（清除旧数据）
2. 重新上传和处理文档

---

## API 接口说明

### 1. 获取推荐模型列表
```
GET /api/embedding/models/recommended
```

**响应示例**:
```json
{
  "status": "ok",
  "models": [
    {
      "name": "BAAI/bge-small-zh-v1.5",
      "description": "中文小型嵌入模型，适合普通硬件，语义理解能力良好",
      "dimension": 512,
      "language": "zh",
      "recommended": true
    }
  ]
}
```

### 2. 获取嵌入服务状态
```
GET /api/embedding/status
```

**响应示例**:
```json
{
  "status": "ok",
  "data": {
    "mode": "local",
    "initialized": true,
    "current_mode": "local",
    "local_model": "BAAI/bge-small-zh-v1.5",
    "config": {
      "local_embedding_model": "BAAI/bge-small-zh-v1.5",
      "openai_embedding_model": "text-embedding-3-small"
    }
  }
}
```

### 3. 设置嵌入模式
```
POST /api/embedding/mode
Content-Type: application/json

{
  "mode": "local",
  "reset_collection": true
}
```

**参数说明**:
- `mode`: 必需，`"local"` 或 `"openai"`
- `reset_collection`: 可选，是否重置向量库（默认 `false`）

### 4. 设置本地嵌入模型
```
POST /api/embedding/local-model
Content-Type: application/json

{
  "model_name": "BAAI/bge-base-zh-v1.5",
  "cache_dir": "/path/to/cache"
}
```

**参数说明**:
- `model_name`: 必需，Hugging Face 模型名称
- `cache_dir`: 可选，模型缓存目录

---

## 常见问题

### Q1: 第一次使用本地模型需要多长时间？
A: 第一次使用时会自动从 Hugging Face 下载模型，时间取决于网络速度和模型大小。`bge-small-zh-v1.5` 约 100MB，通常几分钟内可以完成。

### Q2: 如何更换本地模型？
A: 有两种方式：
1. 修改 `config.json` 中的 `local_embedding_model` 配置
2. 调用 API: `POST /api/embedding/local-model`

**注意**: 更换模型后建议重置向量库。

### Q3: 本地模型保存在哪里？
A: 默认保存在 Hugging Face 的缓存目录中：
- Windows: `C:\Users\&lt;用户名&gt;\.cache\huggingface\hub\`
- Linux/Mac: `~/.cache/huggingface/hub/`

可以通过 `local_model_cache_dir` 配置项自定义缓存位置。

### Q4: 可以在不联网的情况下使用吗？
A: 可以！只要模型已经下载到本地缓存，就可以完全离线使用。

### Q5: 如何从 OpenAI 模式切换到本地模式？
A: 
1. 调用 API: `POST /api/embedding/mode`，设置 `mode` 为 `"local"`，`reset_collection` 为 `true`
2. 或者手动修改 `config.json`，然后重启后端服务并重置向量库

### Q6: 切换模式后旧的文档还在吗？
A: 如果设置了 `reset_collection: true`，向量库会被清空，需要重新上传文档。如果没有重置，旧的文档仍然存在，但由于向量维度可能不同，搜索结果可能不准确。

---

## 依赖安装

确保已安装以下依赖（已包含在 `requirements.txt` 中）：

```bash
pip install sentence-transformers&gt;=2.2.0
```

如果需要加速推理（可选），可以安装 PyTorch with CUDA：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 性能优化建议

1. **使用 GPU 加速**: 如果有 NVIDIA GPU，安装 CUDA 版本的 PyTorch 可以大幅提升推理速度
2. **选择合适的模型**: 普通硬件推荐使用 `bge-small-zh-v1.5`，性能和速度平衡最好
3. **批量处理**: 尽量批量处理文本，而不是单个处理，效率更高

---

## 技术支持

如有问题，请查看日志文件或联系开发团队。
