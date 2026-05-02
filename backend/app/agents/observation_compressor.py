"""
Observation Compressor - 观察结果压缩器
按 observation 类型采用不同压缩策略，防止 Scratchpad 无限膨胀
"""
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ObservationCompressor:

    COMPRESSION_CONFIG = {
        "arxiv_search": {
            "max_papers_in_scratchpad": 5,  # 改为默认 5 篇
            "abstract_max_chars": 150,
            "keep_fields": ["title", "authors", "published", "pdf_url"]
        },
        "weather": {
            "keep_fields": ["city", "temperature", "weather", "humidity", "wind"]
        },
        "default": {
            "max_chars": 500,
            "keep_head": 300,
            "keep_tail": 100
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # 如果有配置，覆盖默认值
        if "arxiv_search" in self.config:
            max_results = self.config["arxiv_search"].get("max_results")
            if max_results:
                self.COMPRESSION_CONFIG["arxiv_search"]["max_papers_in_scratchpad"] = max_results

    def compress(
        self,
        observation: str,
        obs_type: str = "default",
        action_name: str = "",
        max_results_override: Optional[int] = None
    ) -> str:
        if not observation:
            return ""

        if not obs_type or obs_type == "default":
            obs_type = self._infer_type(observation, action_name)

        config = self.COMPRESSION_CONFIG.get(
            obs_type,
            self.COMPRESSION_CONFIG["default"]
        )

        # 如果用户指定了 max_results，覆盖默认值
        if obs_type == "arxiv_search" and max_results_override is not None:
            config = config.copy()
            config["max_papers_in_scratchpad"] = max_results_override

        if obs_type == "arxiv_search":
            return self._compress_arxiv_result(observation, config)
        elif obs_type == "weather":
            return self._compress_weather(observation, config)
        elif obs_type == "error":
            return self._compress_error(observation)
        else:
            return self._compress_generic(observation, config)

    def _infer_type(self, text: str, action_name: str) -> str:
        if action_name == "arxiv-watcher":
            return "arxiv_search"
        if action_name == "amap-weather":
            return "weather"
        if text.startswith("工具执行失败") or text.startswith("Skill execution failed") or "error" in text.lower()[:50]:
            return "error"
        if "### Paper" in text or "Search Results" in text:
            return "arxiv_search"
        return "default"

    def _compress_arxiv_result(self, text: str, config: dict) -> str:
        max_papers = config["max_papers_in_scratchpad"]
        abstract_max = config["abstract_max_chars"]

        papers = re.split(r'(?=### Paper \d+:)', text)

        compressed_parts = []
        paper_count = 0
        header = ""

        for paper_text in papers:
            if not paper_text.strip():
                continue

            if paper_count == 0 and not paper_text.strip().startswith("### Paper"):
                header = paper_text.strip()
                continue

            if paper_count >= max_papers:
                break

            title_match = re.search(r'### Paper \d+: (.+)', paper_text)
            title = title_match.group(1).strip() if title_match else "Unknown"

            abstract_match = re.search(
                r'-\s*\*\*Abstract\*\*:\s*(.+?)(?=\n-|\n\n|$)',
                paper_text, re.DOTALL
            )
            abstract = ""
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                if len(abstract) > abstract_max:
                    abstract = abstract[:abstract_max] + "..."

            pdf_match = re.search(r'-\s*\*\*PDF Link\*\*:\s*(.+)', paper_text)
            pdf_link = pdf_match.group(1).strip() if pdf_match else ""

            authors_match = re.search(r'-\s*\*\*Authors\*\*:\s*(.+)', paper_text)
            authors = authors_match.group(1).strip() if authors_match else ""

            parts = [f"**{title}**"]
            if authors:
                parts.append(f"作者: {authors}")
            if abstract:
                parts.append(f"摘要: {abstract}")
            if pdf_link:
                parts.append(f"链接: {pdf_link}")

            compressed_parts.append("\n".join(parts))
            paper_count += 1

        result = ""
        if header:
            result += header + "\n\n"
        result += "\n\n".join(compressed_parts)

        total_count = len(re.findall(r'### Paper \d+:', text))
        if total_count > max_papers:
            result += f"\n\n*...（共 {total_count} 篇，展示前 {max_papers} 篇）*"

        return result

    def _compress_weather(self, text: str, config: dict) -> str:
        parts = []
        for field in config["keep_fields"]:
            match = re.search(
                rf'[-*]\s*\*\*{field}\*\*:\s*(.+)',
                text, re.IGNORECASE
            )
            if match:
                parts.append(f"{field}: {match.group(1).strip()}")
        return "\n".join(parts) if parts else text[:200]

    def _compress_error(self, text: str) -> str:
        lines = text.split('\n')
        useful_lines = []
        for line in lines:
            if len(useful_lines) >= 3:
                break
            if line.strip().startswith('File "') or (line.strip().startswith('  ') and 'File' in line):
                continue
            useful_lines.append(line)
        return '\n'.join(useful_lines)

    def _compress_generic(self, text: str, config: dict) -> str:
        max_chars = config["max_chars"]
        if len(text) <= max_chars:
            return text

        head = text[:config["keep_head"]]
        tail = text[-config["keep_tail"]:]
        omitted = len(text) - config["keep_head"] - config["keep_tail"]
        return f"{head}\n...\n[中间 {omitted} 字符已省略]\n...\n{tail}"
