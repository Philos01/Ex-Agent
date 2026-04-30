"""
文件摘要生成服务
使用大模型对文件内容进行分析和总结，生成结构化的文件摘要
"""
import logging
import json
from typing import Dict, Any, Optional
from app.core.config import get_complete_config
from openai import OpenAI
import requests

logger = logging.getLogger(__name__)


class DocumentSummary:
    """文档摘要数据结构"""
    
    def __init__(self):
        self.filename: str = ""
        self.summary: str = ""
        self.key_topics: list = []
        self.key_points: list = []
        self.main_conclusions: list = []
        self.technical_terms: list = []
        self.authors: list = []
        self.publication_year: str = ""
        self.venue: str = ""
        self.quality_score: float = 0.0
        self.generated_at: str = ""
        self.file_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "filename": self.filename,
            "summary": self.summary,
            "key_topics": self.key_topics,
            "key_points": self.key_points,
            "main_conclusions": self.main_conclusions,
            "technical_terms": self.technical_terms,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "venue": self.venue,
            "quality_score": self.quality_score,
            "generated_at": self.generated_at,
            "file_path": self.file_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentSummary':
        """从字典创建"""
        summary = cls()
        summary.filename = data.get("filename", "")
        summary.summary = data.get("summary", "")
        summary.key_topics = data.get("key_topics", [])
        summary.key_points = data.get("key_points", [])
        summary.main_conclusions = data.get("main_conclusions", [])
        summary.technical_terms = data.get("technical_terms", [])
        summary.authors = data.get("authors", [])
        summary.publication_year = data.get("publication_year", "")
        summary.venue = data.get("venue", "")
        summary.quality_score = data.get("quality_score", 0.0)
        summary.generated_at = data.get("generated_at", "")
        summary.file_path = data.get("file_path", "")
        return summary


class DocumentSummarizer:
    """文档摘要生成器"""
    
    def __init__(self):
        self.cfg = get_complete_config()
    
    def _get_openai_client(self):
        """获取OpenAI客户端"""
        key = self.cfg.get("openai_api_key")
        base_url = self.cfg.get("openai_base_url")
        
        client_kwargs = {}
        if key:
            client_kwargs["api_key"] = key
        if base_url:
            client_kwargs["base_url"] = base_url
        
        return OpenAI(**client_kwargs)
    
    def generate_summary(self, file_text: str, filename: str, provider: str = "openai") -> DocumentSummary:
        """
        生成文档摘要
        
        Args:
            file_text: 文件完整文本
            filename: 文件名
            provider: LLM提供商
            
        Returns:
            DocumentSummary对象
        """
        import datetime
        
        logger.info(f"开始生成文档摘要: {filename}")
        
        # 构建提示词
        system_prompt = """你是一个专业的学术文献分析专家，专门用于分析和总结知识库中的学术论文。

你的任务是分析提供的学术论文内容，生成结构化的摘要，遵循以下要求：

1. 保持学术严谨性和准确性，所有内容必须严格基于提供的文档
2. 提取论文的核心研究主题
3. 列出关键要点（3-5条），包括方法创新点和实验结论
4. 总结主要结论（2-3条）
5. 提取论文中出现的重要技术术语和方法名称
6. 如果能识别，请提取论文的作者信息、发表年份和期刊/会议信息
7. 绝不编造文档中未提及的任何信息

请以JSON格式输出，包含以下字段：
{
  "summary": "论文的简要总结（100-200字），包含研究问题、方法和主要结论",
  "key_topics": ["核心主题1", "核心主题2"],
  "key_points": ["关键要点1", "关键要点2", "关键要点3"],
  "main_conclusions": ["主要结论1", "主要结论2"],
  "technical_terms": ["术语1", "术语2"],
  "authors": ["作者1", "作者2"],
  "publication_year": "发表年份（如无法确定则为空字符串）",
  "venue": "发表期刊或会议名称（如无法确定则为空字符串）",
  "quality_score": 0.9
}

其中 quality_score 是你对文档摘要质量的评分（0.0-1.0），基于：
- 摘要的准确性
- 信息的完整性
- 结构的清晰度

重要：authors、publication_year、venue 字段必须从文档内容中提取，如果文档中没有明确提及，请留空字符串，绝不可猜测或编造。
"""

        # 限制文本长度，避免token超限
        max_text_length = 15000
        if len(file_text) > max_text_length:
            file_text = file_text[:max_text_length]
            logger.warning(f"文档文本过长，已截断为 {max_text_length} 字符")
        
        user_prompt = f"请分析以下文档内容，生成结构化摘要：\n\n文件名：{filename}\n\n文档内容：\n{file_text}"
        
        try:
            if provider == "ollama":
                result = self._generate_with_ollama(system_prompt, user_prompt)
            else:
                result = self._generate_with_openai(system_prompt, user_prompt)
            
            # 解析结果
            doc_summary = DocumentSummary()
            doc_summary.filename = filename
            doc_summary.generated_at = datetime.datetime.utcnow().isoformat()
            
            if result:
                try:
                    data = json.loads(result)
                    doc_summary.summary = data.get("summary", "")
                    doc_summary.key_topics = data.get("key_topics", [])
                    doc_summary.key_points = data.get("key_points", [])
                    doc_summary.main_conclusions = data.get("main_conclusions", [])
                    doc_summary.technical_terms = data.get("technical_terms", [])
                    doc_summary.authors = data.get("authors", [])
                    doc_summary.publication_year = data.get("publication_year", "")
                    doc_summary.venue = data.get("venue", "")
                    doc_summary.quality_score = data.get("quality_score", 0.5)
                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")
                    # 如果JSON解析失败，尝试提取文本
                    doc_summary.summary = result
            
            logger.info(f"文档摘要生成成功: {filename}")
            return doc_summary
            
        except Exception as e:
            logger.error("Summary generation failed: %s", e, exc_info=True)
            # 返回一个简单的摘要
            doc_summary = DocumentSummary()
            doc_summary.filename = filename
            doc_summary.summary = f"文档：{filename}"
            doc_summary.generated_at = datetime.datetime.utcnow().isoformat()
            return doc_summary
    
    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """使用OpenAI生成摘要"""
        try:
            client = self._get_openai_client()
            model_name = self.cfg.get("openai_chat_model", "gpt-3.5-turbo")
            
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            
            if (
                completion.choices 
                and len(completion.choices) > 0 
                and completion.choices[0].message 
                and completion.choices[0].message.content
            ):
                return completion.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.error(f"OpenAI 摘要生成失败: {e}")
            return None
    
    def _generate_with_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """使用Ollama生成摘要"""
        try:
            endpoint = self.cfg.get("ollama_url", "http://localhost:11434").rstrip("/") + "/api/generate"
            model_name = self.cfg.get("ollama_model", "llama2")
            
            prompt = f"{system_prompt}\n\n{user_prompt}"
            
            r = requests.post(
                endpoint,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2000
                    }
                },
                timeout=self.cfg.get("timeouts", {}).get("document_summary", 300)
                if self.cfg.get("timeouts", {}).get("enabled", True) else None
            )
            r.raise_for_status()
            
            result = r.json().get("response", "")
            return result.strip() if result else None
        except Exception as e:
            logger.error(f"Ollama 摘要生成失败: {e}")
            return None


# 全局摘要生成器实例
_summarizer = None


def get_document_summarizer() -> DocumentSummarizer:
    """
    获取或创建全局文档摘要生成器实例
    
    Returns:
        DocumentSummarizer 实例
    """
    global _summarizer
    if _summarizer is None:
        _summarizer = DocumentSummarizer()
    return _summarizer


def generate_document_summary(file_text: str, filename: str, provider: str = "openai") -> DocumentSummary:
    """
    便捷函数：生成文档摘要
    
    Args:
        file_text: 文件完整文本
        filename: 文件名
        provider: LLM提供商
        
    Returns:
        DocumentSummary对象
    """
    summarizer = get_document_summarizer()
    return summarizer.generate_summary(file_text, filename, provider)
