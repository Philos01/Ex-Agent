"""
Entity Extractor — LLM-driven, zero hardcoded entity types.

The LLM reads document content and decides what entity types exist.
No predefined schema. Works for papers, meeting notes, code docs, etc.
"""
import json
import hashlib
import logging
import re
from typing import Dict, List, Any, Optional

from app.core.config import get_complete_config

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "1.1.0"

ENTITY_EXTRACTION_PROMPT = """你是一个知识图谱实体提取器。

# 核心原则
1. 图数据库只存储：
   - 明确的事实（"张三在宁波拓普工作"）
   - 实体间的直接关系（"张三-工作单位-宁波拓普"）
2. 需要推理、需要详细解释的内容，不提取关系，留待父子检索处理

# 提取规则
1. 实体类型：
   - 人物：人名、昵称
   - 组织：公司、学校、机构、实验室
   - 概念：方法、模型、技术、指标、数据集
   - 文档：论文、报告、笔记、代码文件
   - 其他：根据内容决定

2. 关系类型：
   - 仅提取明确、直接的关系
   - 例如："工作单位"、"毕业于"、"使用"、"包含"
   - 不确定的关系不提取

3. 对于每个实体：
   - type：实体类型
   - name：简洁唯一的名称
   - description：一句话描述
   - properties：结构化属性（如果有），必须是标准JSON对象，例如：
     - 人物实体：{"职位": "工程师", "学校": "清华大学"}
     - 组织实体：{"位置": "宁波", "类型": "公司"}
     - 文档实体：{"作者": "张三", "年份": "2025"}

# 文档
$text

# 输出 JSON 格式
{
  "entities": [
    { "type": "类型", "name": "名称", "description": "描述", "properties": { "可选属性": "值" } }
  ],
  "relations": [
    { "source": "实体A", "target": "实体B", "type": "关系类型", "description": "关系说明" }
  ]
}

⚠️ 重要：
- properties 必须是标准 JSON 对象，键名不能包含空格或特殊字符
- 所有字符串必须用双引号包围
- 只输出 JSON，不要其他文本、说明或markdown格式
- 如果没有实体或关系，返回空数组"""


class EntityExtractor:
    """
    Extracts entities and relations from document text using LLM.

    Features:
    - Zero hardcoded entity types (LLM decides)
    - Rule-based pre-extraction from filename patterns
    - Entity disambiguation via embedding similarity
    - Result caching by content hash
    """

    def __init__(self, provider: str = "openai", cache_size: int = 200):
        self.provider = provider
        self.cfg = get_complete_config()
        self._cache: Dict[str, Dict] = {}
        self._cache_order: list = []
        self._cache_max = cache_size

    def extract(
        self,
        text: str,
        filename: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract entities and relations from document text.

        Returns:
            {"entities": [...], "relations": [...]}
        """
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        if content_hash in self._cache:
            logger.info("[EntityExtractor] Cache hit: %s", filename)
            return self._cache[content_hash]

        prov = provider or self.provider

        # Phase 1: rule-based pre-extraction from filename
        rule_entities = self._extract_from_filename(filename)

        # Phase 2: LLM extraction
        from string import Template
        prompt_template = Template(ENTITY_EXTRACTION_PROMPT)
        prompt = prompt_template.safe_substitute(text=text[:8000])
        llm_result = self._call_llm(prompt, prov)

        if not llm_result:
            result = {"entities": rule_entities, "relations": []}
        else:
            llm_entities = llm_result.get("entities", [])
            llm_relations = llm_result.get("relations", [])
            merged_entities = self._merge_entities(rule_entities, llm_entities)
            result = {"entities": merged_entities, "relations": llm_relations}

        for entity in result["entities"]:
            if "properties" not in entity:
                entity["properties"] = {}

        if len(self._cache_order) >= self._cache_max:
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)
        self._cache[content_hash] = result
        self._cache_order.append(content_hash)
        logger.info(
            "[EntityExtractor] %s → %d entities, %d relations",
            filename,
            len(result["entities"]),
            len(result["relations"]),
        )
        return result

    def _extract_from_filename(self, filename: str) -> List[Dict]:
        """Rule-based entity extraction from filename patterns."""
        entities = []
        base = filename.rsplit(".", 1)[0]  # remove extension

        # Pattern: "作者-标题-期刊" or "作者-标题-期刊.md"
        # Also handles Chinese names
        parts = base.replace("_", "-").split("-")

        # Check last segment for known venue patterns
        venue_keywords = [
            "TGRS", "JSTRAS", "TIP", "CVPR", "ICCV", "ECCV", "NeurIPS",
            "ICML", "AAAI", "IJCAI", "遥感", "测绘", "电子",
        ]
        last = parts[-1].strip().upper() if parts else ""
        for kw in venue_keywords:
            if kw.upper() in last:
                entities.append({"type": "期刊/会议", "name": parts[-1].strip(),
                                 "description": f"发表于 {parts[-1].strip()}"})
                parts = parts[:-1]
                break

        # Check first segment for Chinese name pattern (2-3 chars)
        if parts and len(parts[0].strip()) <= 4 and re.search(r'[一-鿿]', parts[0]):
            entities.append({"type": "作者", "name": parts[0].strip(),
                             "description": f"文档作者: {parts[0].strip()}"})

        # Year pattern in filename
        for p in parts:
            m = re.search(r'(20\d{2})', p)
            if m:
                entities.append({"type": "年份", "name": m.group(1),
                                 "description": f"发表于 {m.group(1)} 年"})

        return entities

    def _merge_entities(
        self, rule_entities: List[Dict], llm_entities: List[Dict]
    ) -> List[Dict]:
        merged = list(rule_entities)
        rule_names = {e["name"].lower() for e in rule_entities}
        for ent in llm_entities:
            name = ent.get("name", "").strip()
            if name and name.lower() not in rule_names:
                if "properties" not in ent:
                    ent["properties"] = {}
                merged.append(ent)
                rule_names.add(name.lower())
            elif name and name.lower() in rule_names:
                for existing in merged:
                    if existing["name"].lower() == name.lower():
                        existing_props = existing.get("properties", {})
                        new_props = ent.get("properties", {})
                        existing["properties"] = {**new_props, **existing_props}
                        break
        for entity in merged:
            if "properties" not in entity:
                entity["properties"] = {}
        return merged

    def _call_llm(self, prompt: str, provider: str) -> Optional[Dict]:
        from app.agents.llm_client import create_llm_client
        client = create_llm_client()
        try:
            result = client.complete_json(
                prompt=prompt, provider=provider,
                system_prompt="You are a knowledge graph entity extractor. Output only valid JSON.",
            )
            # 验证和清理结果
            if result:
                # 确保 entities 是列表
                entities = result.get("entities", [])
                if not isinstance(entities, list):
                    entities = []
                # 清理每个实体
                for i, ent in enumerate(entities):
                    if not isinstance(ent, dict):
                        ent = {}
                    # 确保 properties 是字典
                    if "properties" not in ent or not isinstance(ent["properties"], dict):
                        ent["properties"] = {}
                    else:
                        # 清理 properties 的键名（去除前后空格）
                        clean_props = {}
                        for k, v in ent["properties"].items():
                            clean_k = k.strip()
                            if clean_k:
                                clean_props[clean_k] = v
                        ent["properties"] = clean_props
                    # 确保 name 存在
                    if "name" not in ent:
                        ent["name"] = ""
                    # 清理 name 和 description
                    ent["name"] = ent.get("name", "").strip()
                    ent["description"] = ent.get("description", "").strip()
                    entities[i] = ent
                result["entities"] = entities
                
                # 确保 relations 是列表
                relations = result.get("relations", [])
                if not isinstance(relations, list):
                    relations = []
                result["relations"] = relations
                
                return result
            return None
        except Exception as e:
            logger.warning(f"LLM extraction failed, falling back: {e}")
            return {"entities": [], "relations": []}

    def clear_cache(self):
        self._cache.clear()
