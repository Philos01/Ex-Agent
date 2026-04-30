"""
Observer - Enhanced Observation Module

Processes and compresses tool execution results for LLM consumption.
Type-aware compression strategies prevent scratchpad bloat.
"""
import logging
import re
from typing import Dict, Any, Optional

from app.agents.types import ActionResult

logger = logging.getLogger(__name__)


class Observer:
    """Observation processor with type-aware compression."""

    COMPRESSION_CONFIG: Dict[str, dict] = {
        "arxiv_search": {
            "max_papers_in_scratchpad": 3,
            "abstract_max_chars": 150,
        },
        "weather": {
            "keep_fields": ["city", "temperature", "weather", "humidity", "wind"],
        },
        "default": {
            "max_chars": 500,
            "keep_head": 300,
            "keep_tail": 100,
        },
    }

    def process(self, result: ActionResult) -> Dict[str, Any]:
        """
        Process an action result into an observation summary.

        Returns dict with 'compressed' (for LLM), 'raw' (for UI), and metadata.
        """
        obs_type = self._infer_type(result)

        compressed = self.compress(result.output, obs_type, result.tool_name)

        return {
            "compressed": compressed,
            "raw": result.output,
            "raw_length": len(result.output),
            "compressed_length": len(compressed),
            "success": result.success,
            "tool_name": result.tool_name,
            "execution_time_ms": result.execution_time_ms,
        }

    def compress(
        self,
        text: str,
        obs_type: str = "default",
        tool_name: str = "",
    ) -> str:
        """Compress observation text by type."""
        if not text:
            return ""

        # Auto-detect obs_type from tool_name if not specified
        if obs_type == "default" and tool_name:
            if tool_name == "arxiv-watcher":
                obs_type = "arxiv_search"
            elif tool_name == "amap-weather":
                obs_type = "weather"

        config = self.COMPRESSION_CONFIG.get(obs_type, self.COMPRESSION_CONFIG["default"])

        if obs_type == "arxiv_search":
            return self._compress_arxiv(text, config)
        elif obs_type == "weather":
            return self._compress_weather(text, config)
        elif obs_type == "error":
            return self._compress_error(text)
        else:
            return self._compress_generic(text, config)

    def _infer_type(self, result: ActionResult) -> str:
        tool = result.tool_name
        text = result.output[:200]
        if tool == "arxiv-watcher":
            return "arxiv_search"
        if tool == "amap-weather":
            return "weather"
        if not result.success or "error" in text.lower():
            return "error"
        if "### Paper" in text or "Search Results" in text:
            return "arxiv_search"
        return "default"

    def _compress_arxiv(self, text: str, config: dict) -> str:
        max_papers = config["max_papers_in_scratchpad"]
        abstract_max = config["abstract_max_chars"]
        papers = re.split(r"(?=### Paper \d+:)", text)

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

            title_match = re.search(r"### Paper \d+: (.+)", paper_text)
            title = title_match.group(1).strip() if title_match else "Unknown"

            abstract_match = re.search(r"-\s*\*\*Abstract\*\*:\s*(.+?)(?=\n-|\n\n|$)", paper_text, re.DOTALL)
            abstract = ""
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                if len(abstract) > abstract_max:
                    abstract = abstract[:abstract_max] + "..."

            pdf_match = re.search(r"-\s*\*\*PDF Link\*\*:\s*(.+)", paper_text)
            pdf_link = pdf_match.group(1).strip() if pdf_match else ""

            authors_match = re.search(r"-\s*\*\*Authors\*\*:\s*(.+)", paper_text)
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

        total_count = len(re.findall(r"### Paper \d+:", text))
        if total_count > max_papers:
            result += f"\n\n*...（共 {total_count} 篇，展示前 {max_papers} 篇）*"
        return result

    def _compress_weather(self, text: str, config: dict) -> str:
        parts = []
        for field in config["keep_fields"]:
            match = re.search(rf'[-*]\s*\*\*{field}\*\*:\s*(.+)', text, re.IGNORECASE)
            if match:
                parts.append(f"{field}: {match.group(1).strip()}")
        return "\n".join(parts) if parts else text[:200]

    def _compress_error(self, text: str) -> str:
        lines = text.split("\n")
        useful = []
        for line in lines:
            if len(useful) >= 3:
                break
            if line.strip().startswith('File "') or ("File" in line and line.strip().startswith("  ")):
                continue
            useful.append(line)
        return "\n".join(useful)

    def _compress_generic(self, text: str, config: dict) -> str:
        max_chars = config["max_chars"]
        if len(text) <= max_chars:
            return text
        head = text[: config["keep_head"]]
        tail = text[-config["keep_tail"] :]
        omitted = len(text) - config["keep_head"] - config["keep_tail"]
        return f"{head}\n...\n[中间 {omitted} 字符已省略]\n...\n{tail}"
