
"""
Skill Selector - LLM-based skill selection with zero hardcoded rules.
Decisions are made purely by the LLM reading each skill's self-description.
"""
import logging
import json
import hashlib
import re
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import get_complete_config
from app.skills.metadata_parser import get_skill_metadata
from openai import OpenAI

logger = logging.getLogger(__name__)


class DecisionCache:
    """Lightweight cache for skill selection decisions to reduce LLM calls."""

    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.RLock()

    @staticmethod
    def _normalize(text: str) -> str:
        t = re.sub(r'[^\w一-鿿]', '', text.lower())
        return t

    def _key(self, question: str, provider: str) -> str:
        raw = f"{self._normalize(question)}|{provider}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, question: str, provider: str):
        with self._lock:
            key = self._key(question, provider)
            entry = self._cache.get(key)
            if entry is None:
                return None
            ts, value = entry
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            logger.info("[DecisionCache] Cache hit for question hash=%s", key[:8])
            return value

    def put(self, question: str, provider: str, result):
        with self._lock:
            key = self._key(question, provider)
            self._cache[key] = (time.time(), result)
            if len(self._cache) > 500:
                oldest = min(self._cache.items(), key=lambda x: x[1][0])
                del self._cache[oldest[0]]

    def invalidate(self):
        with self._lock:
            self._cache.clear()
            logger.info("[DecisionCache] Cache invalidated")


class SkillSelector:
    """
    LLM-based skill selector with zero hardcoded rules.

    The LLM decides purely by reading each skill's description, which includes
    "Use when" and "Do NOT use when" guidance. No skill names or trigger keywords
    are hardcoded in the prompt or in this code.
    """

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skill_metadata: Dict[str, Dict[str, Any]] = {}
        self.cfg = get_complete_config()
        self._cache = DecisionCache(ttl_seconds=60)
        self._load_all_skill_metadata()

    def _load_all_skill_metadata(self):
        if not self.skills_dir.exists():
            logger.warning("Skills directory not found: %s", self.skills_dir)
            return

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                try:
                    metadata = get_skill_metadata(skill_dir)
                    skill_name = metadata["name"]
                    self._skill_metadata[skill_name] = {
                        **metadata,
                        "dir": skill_dir,
                    }
                    logger.info("Loaded skill metadata: %s", skill_name)
                except Exception as e:
                    logger.error(
                        "Failed to load skill metadata from %s: %s", skill_dir, e,
                        exc_info=True,
                    )

    def get_available_skills(self) -> List[Dict[str, Any]]:
        return list(self._skill_metadata.values())

    def get_skill_dir(self, skill_name: str) -> Optional[Path]:
        if skill_name in self._skill_metadata:
            return self._skill_metadata[skill_name]["dir"]
        return None

    def invalidate_cache(self):
        self._cache.invalidate()

    def _call_llm(self, prompt: str, provider: str) -> str:
        from app.agents.llm_client import create_llm_client
        client = create_llm_client()
        return client.complete(
            prompt=prompt, provider=provider,
            system_prompt="You are a skill selector. Output only valid JSON.",
        )

    # ── prompt builder (zero hardcoded rules) ──────────────────────

    def _build_selection_prompt(
        self,
        question: str,
        conversation_history: str = "",
    ) -> str:
        """Build a generic skill-selection prompt.  No skill names or trigger
        keywords are hardcoded — the LLM reads each skill's self-description."""
        skills_info: List[Dict[str, Any]] = []
        for skill in self.get_available_skills():
            skills_info.append({
                "name": skill["name"],
                "description": skill.get("description", ""),
                "input_parameters": skill.get("input_parameters", {}),
            })

        context_block = ""
        if conversation_history:
            context_block = f"""
## Recent Conversation Context
{conversation_history}

Use the conversation context to understand follow-up questions.  If the user
says "那明天呢？" after a weather query, that likely refers to the same
skill the conversation has been using.
"""

        return f"""# Skill Selection Task

You are a skill selector for an AI assistant.  Decide whether any of the
available skills should be invoked to answer the user's question.

## Available Skills
{json.dumps(skills_info, ensure_ascii=False, indent=2)}

## User Question
{question}
{context_block}
## Instructions

1. Read each skill's **description** carefully — it contains both "Use when"
   and "Do NOT use when" guidance written by the skill's author.
2. If a skill's description clearly matches the user's intent, select it.
3. If **no** skill matches, return should_use_skill: false.
4. Extract parameters from the question according to the skill's
   **input_parameters** schema — use the exact parameter names defined there.
5. If the conversation context suggests a follow-up related to a previously
   used topic, prefer the skill that matches that topic.

## Output JSON schema
{{
  "should_use_skill": boolean,
  "skill_name": null,
  "parameters": {{}},
  "reasoning": "one sentence explaining why you chose or rejected skills"
}}

Output **only** the JSON, no other text."""

    # ── public API ────────────────────────────────────────────────

    def select_skill_with_llm(
        self,
        question: str,
        provider: str = "openai",
        conversation_history: str = "",
        use_cache: bool = True,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Select skill using LLM with zero hardcoded rules.

        Args:
            question: User question
            provider: LLM provider ("openai" or "ollama")
            conversation_history: Optional recent conversation context
            use_cache: Whether to check/populate the decision cache

        Returns:
            (should_use, skill_name, params)
        """
        available_skills = self.get_available_skills()
        if not available_skills:
            return False, None, None

        # cache check
        if use_cache:
            cached = self._cache.get(question, provider)
            if cached is not None:
                return cached

        logger.info("[SkillSelector] Selecting skill for: %s", question[:80])

        prompt = self._build_selection_prompt(question, conversation_history)

        try:
            response_text = self._call_llm(prompt, provider)

            if not response_text:
                logger.warning("[SkillSelector] Empty LLM response")
                return False, None, None

            result = self._parse_response(response_text)
            if result is None:
                return False, None, None

            should_use, skill_name, params = result

            # validate skill exists
            if should_use and skill_name and skill_name in self._skill_metadata:
                logger.info(
                    "[SkillSelector] Selected: %s, params: %s", skill_name, params
                )
                if use_cache:
                    self._cache.put(question, provider, result)
                return result

            logger.info("[SkillSelector] No skill selected or skill not found")
            if use_cache:
                self._cache.put(question, provider, (False, None, None))
            return False, None, None

        except Exception as e:
            logger.error("[SkillSelector] LLM call failed: %s", e, exc_info=True)
            return False, None, None

    def _parse_response(
        self, response_text: str
    ) -> Optional[Tuple[bool, Optional[str], Optional[Dict[str, Any]]]]:
        """Extract JSON decision from LLM response."""
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")
        if json_start == -1 or json_end == -1:
            logger.warning("[SkillSelector] No JSON found in response")
            return None

        try:
            json_str = response_text[json_start : json_end + 1]
            data = json.loads(json_str)
            should_use = data.get("should_use_skill", False)
            skill_name = data.get("skill_name")
            params = data.get("parameters", {})
            reasoning = data.get("reasoning", "")
            if reasoning:
                logger.info("[SkillSelector] Reasoning: %s", reasoning)
            return should_use, skill_name, params
        except json.JSONDecodeError as e:
            logger.warning("[SkillSelector] Invalid JSON: %s", e)
            return None
