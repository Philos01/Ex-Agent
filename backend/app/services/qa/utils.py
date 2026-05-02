"""
QA utility functions — formatting, output regularization, LLM client factory.
"""
import re
import logging
from typing import Tuple, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


def format_conversation_history(messages: list) -> str:
    """Format recent messages as conversation context for prompts."""
    if not messages:
        return ""
    result = "### 💬 对话历史：\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            result += f"用户: {content}\n"
        elif role == "assistant":
            result += f"助手: {content}\n"
        skill_result = msg.get("skill_result")
        if skill_result:
            skill_name = msg.get("skill_name")
            prefix = f"[技能结果 - {skill_name}]" if skill_name else "[技能结果]"
            result += f"{prefix} {skill_result}\n"
    result += "\n"
    return result


def regularize_output(text: str) -> str:
    """Post-process LLM output: Markdown headings → HTML, list formatting, etc."""
    if not text:
        return text

    text = re.sub(r'^\s*###\s+(.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*##\s+(.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*#\s+(.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)

    lines = text.split('\n')
    optimized_lines = []
    in_list = False
    list_type = ''

    for line in lines:
        if re.match(r'^\s*\d+\s*[.,)]\s*', line):
            if not in_list or list_type != 'numbered':
                optimized_lines.append('<ol>')
                in_list = True
                list_type = 'numbered'
            item = re.sub(r'^\s*\d+\s*[.,)]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        elif re.match(r'^\s*[•●○▸▶►-\*]\s*', line):
            if not in_list or list_type != 'bulleted':
                optimized_lines.append('<ul>')
                in_list = True
                list_type = 'bulleted'
            item = re.sub(r'^\s*[•●○▸▶►-\*]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        else:
            if in_list:
                optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')
                in_list = False
                list_type = ''
            optimized_lines.append(line)

    if in_list:
        optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')

    text = '\n'.join(optimized_lines)
    text = re.sub(r'\b([A-Z]{2,})\b', r'<span class="font-bold">\1</span>', text)
    text = re.sub(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', r'<span class="font-italic">\1</span>', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    paragraphs = []
    current_paragraph = []
    for line in text.split('\n'):
        if line.strip() == '' or line.startswith('<h') or line.startswith('<ul') or line.startswith('<ol') or line.startswith('</'):
            if current_paragraph:
                paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
            paragraphs.append(line)
        else:
            current_paragraph.append(line)
    if current_paragraph:
        paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')

    return '\n'.join(paragraphs).strip()


def get_client_for_provider(cfg: dict, provider: str, enable_thinking: bool = False):
    """
    Returns (OpenAI client, model_name) for the given provider.
    DeepSeek uses the OpenAI SDK with deepseek base_url.
    Ollama returns (None, model_name) — caller must handle separately.
    """
    if provider == "ollama":
        return None, cfg.get("ollama_model", "")

    if provider == "deepseek":
        api_key = cfg.get("deepseek_api_key")
        base_url = cfg.get("deepseek_base_url", "https://api.deepseek.com/v1")
        model = (cfg.get("deepseek_reasoner_model", "deepseek-reasoner")
                 if enable_thinking
                 else cfg.get("deepseek_chat_model", "deepseek-chat"))
    else:
        api_key = cfg.get("openai_api_key")
        base_url = cfg.get("openai_base_url")
        model = cfg.get("openai_chat_model", "gpt-3.5-turbo")

    client_kwargs: dict = {}
    if api_key:
        client_kwargs["api_key"] = api_key
    if base_url:
        client_kwargs["base_url"] = base_url
    client_kwargs["timeout"] = 60.0
    return OpenAI(**client_kwargs), model


def get_openai_client(cfg: dict):
    """Legacy helper — returns an OpenAI client for the configured provider."""
    client, _ = get_client_for_provider(cfg, cfg.get("provider", "openai"))
    return client
