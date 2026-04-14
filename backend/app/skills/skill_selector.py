
"""
Skill Selector - Select skills using LLM based on YAML frontmatter
"""
import logging
import json
import requests
from pathlib import Path
from app.core.config import load_config
from app.skills.metadata_parser import get_skill_metadata
from openai import OpenAI

logger = logging.getLogger(__name__)


class SkillSelector:
    """
    Skill Selector - Select skills based on LLM and YAML frontmatter
    """
    
    def __init__(self, skills_dir):
        self.skills_dir = skills_dir
        self._skill_metadata = {}
        self.cfg = load_config()
        self._load_all_skill_metadata()
    
    def _load_all_skill_metadata(self):
        """Load YAML frontmatter from all skill packages"""
        if not self.skills_dir.exists():
            logger.warning("Skills directory not found: {}".format(self.skills_dir))
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                try:
                    metadata = get_skill_metadata(skill_dir)
                    skill_name = metadata["name"]
                    self._skill_metadata[skill_name] = {
                        **metadata,
                        "dir": skill_dir
                    }
                    logger.info("Loaded skill metadata: {}".format(skill_name))
                except Exception as e:
                    logger.error("Failed to load skill metadata from {}: {}".format(skill_dir, e), exc_info=True)
    
    def get_available_skills(self):
        """Get list of all available skill metadata"""
        return list(self._skill_metadata.values())
    
    def _get_openai_client(self):
        """获取OpenAI客户端实例"""
        key = self.cfg.get("openai_api_key")
        base_url = self.cfg.get("openai_base_url")
        
        client_kwargs = {}
        if key:
            client_kwargs["api_key"] = key
        if base_url:
            client_kwargs["base_url"] = base_url
        
        return OpenAI(**client_kwargs)
    
    def _call_ollama(self, prompt):
        """调用Ollama模型（非流式）"""
        try:
            endpoint = self.cfg.get("ollama_url").rstrip("/") + "/api/generate"
            model_name = self.cfg.get("ollama_model")
            logger.info(f"[SkillSelector-By-LLM] Calling Ollama with model: {model_name}")
            
            # 设置 stream=False 确保返回单个 JSON 对象而不是流式响应
            r = requests.post(endpoint, json={"model": model_name, "prompt": prompt, "stream": False}, timeout=60)
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"[SkillSelector-By-LLM] Ollama call failed: {str(e)}")
            raise
    
    def _call_openai(self, prompt):
        """调用OpenAI模型"""
        client = self._get_openai_client()
        model_name = self.cfg.get("openai_chat_model", "gpt-3.5-turbo")
        
        logger.info(f"[SkillSelector-By-LLM] Calling OpenAI with model: {model_name}")
        
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a skill selector that outputs only JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=512,
            temperature=0.1,
        )
        
        if (
            completion.choices 
            and len(completion.choices) > 0 
            and completion.choices[0].message 
            and completion.choices[0].message.content
        ):
            return completion.choices[0].message.content.strip()
        return ""
    
    def select_skill_with_llm(self, question, provider="openai"):
        """
        Select skill using LLM
        
        Args:
            question: User question
            provider: LLM provider ("openai" or "ollama")
            
        Returns:
            (should_use, skill_name, skill_params)
        """
        available_skills = self.get_available_skills()
        
        if not available_skills:
            return False, None, None
        
        logger.info("[SkillSelector-By-LLM] Selecting skill for question: {}".format(question))
        
        # Build skills metadata string for LLM
        skills_info = []
        for skill in available_skills:
            skills_info.append({
                "name": skill["name"],
                "description": skill.get("description", ""),
                "input_parameters": skill.get("input_parameters", {})
            })
        
        # LLM prompt
        prompt = f"""
# Skill Selection Task

You are a skill selector for an AI assistant. Your task is to analyze the user's question and determine if any of the available skills should be used.

## Available Skills:
{json.dumps(skills_info, ensure_ascii=False, indent=2)}

## User Question:
{question}

## Instructions:
1. Carefully read the user's question
2. Compare the question with each skill's description
3. Determine if any skill is appropriate for this question
4. If a skill is appropriate, extract the necessary parameters from the question
5. Output your decision in JSON format

## Output JSON Schema:
{{
  "should_use_skill": boolean,
  "skill_name": string | null,
  "parameters": {{
    "query": string (for search-related skills),
    "location": string (for weather-related skills)
  }}
}}

## Important Notes:
- Set "should_use_skill" to true only if the question clearly matches a skill's purpose
- Extract parameters directly from the question
- If no skill matches, set "should_use_skill" to false and "skill_name" to null
- Be conservative - only use skills when they are clearly relevant
- Output only the JSON, no other text
"""
        
        try:
            # 根据provider选择调用方式
            if provider == "ollama":
                response_text = self._call_ollama(prompt)
            else:
                response_text = self._call_openai(prompt)
            print(f"[SkillSelector-By-LLM] Using provider: {provider}")
            if not response_text:
                logger.warning("[SkillSelector-By-LLM] Empty LLM response")
                return False, None, None
            
            # Extract JSON from response (in case of extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end + 1]
                result = json.loads(json_str)
                
                should_use = result.get("should_use_skill", False)
                skill_name = result.get("skill_name")
                params = result.get("parameters", {})
                
                # Validate skill name exists
                if should_use and skill_name and skill_name in self._skill_metadata:
                    logger.info(f"[SkillSelector-By-LLM] Selected skill: {skill_name}, params: {params}")
                    return should_use, skill_name, params
                else:
                    logger.info(f"[SkillSelector-By-LLM] No skill selected or skill not found")
                    return False, None, None
            
            logger.warning("[SkillSelector-By-LLM] Invalid LLM response format")
            return False, None, None
            
        except Exception as e:
            logger.error(f"[SkillSelector-By-LLM] LLM call failed: {e}", exc_info=True)
            return False, None, None
    
    def get_skill_dir(self, skill_name):
        """Get skill package directory"""
        if skill_name in self._skill_metadata:
            return self._skill_metadata[skill_name]["dir"]
        return None

