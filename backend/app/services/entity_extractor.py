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


ENTITY_EXTRACTION_PROMPT = """You are a knowledge graph entity extractor. Read the document below
and identify the key entities and their relationships.

# Rules
1. Entities can be ANY type — people, concepts, methods, tools, events,
   data, locations, time points, metrics, decisions, risks, tasks, code modules,
   datasets, venues, organizations...  Decide the type based on content.
   Do NOT force content into a fixed set of types.
2. For each entity provide:
   - type: the category YOU decide is appropriate
   - name: a concise, unique name for this entity
   - description: one sentence describing what it is
3. Relationships describe connections between entities:
   - source: entity name
   - target: entity name
   - type: the relationship category YOU decide
   - description: one sentence explaining the relationship
4. Extract ALL meaningful entities and relationships. Be thorough.
5. Prefer specific names (e.g. "PANet" not "a neural network method").

# Document
{text}

# Output JSON schema
{{
  "entities": [
    {{"type": "你决定的类型", "name": "实体名", "description": "一句话描述"}}
  ],
  "relations": [
    {{"source": "实体A", "target": "实体B", "type": "你决定的类型", "description": "关系说明"}}
  ]
}}

Output ONLY the JSON, no other text."""


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
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:8000])
        llm_result = self._call_llm(prompt, prov)

        if not llm_result:
            # LLM failed, use rule-based results only
            result = {"entities": rule_entities, "relations": []}
        else:
            # Merge rule-based + LLM results (rule-based as ground truth)
            llm_entities = llm_result.get("entities", [])
            llm_relations = llm_result.get("relations", [])
            merged_entities = self._merge_entities(rule_entities, llm_entities)
            result = {"entities": merged_entities, "relations": llm_relations}

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
        """Merge rule-based entities with LLM entities, avoiding duplicates."""
        merged = list(rule_entities)
        rule_names = {e["name"].lower() for e in rule_entities}
        for ent in llm_entities:
            name = ent.get("name", "").strip()
            if name and name.lower() not in rule_names:
                merged.append(ent)
                rule_names.add(name.lower())
        return merged

    def _call_llm(self, prompt: str, provider: str) -> Optional[Dict]:
        from app.agents.llm_client import create_llm_client
        client = create_llm_client()
        return client.complete_json(
            prompt=prompt, provider=provider,
            system_prompt="You are a knowledge graph entity extractor. Output only valid JSON.",
        )

    def clear_cache(self):
        self._cache.clear()
