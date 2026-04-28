---
name: arxiv-watcher
description: |
  Search and summarize papers from the external ArXiv database (arxiv.org). 
  
  USE THIS SKILL WHEN:
  - User asks for latest/newest/recent research in any field (keywords: "最新", "latest", "最近", "前沿", "最新进展")
  - User says "搜索" + "最新" together (e.g., "帮我搜索一下关于光谱超分的最新文章")
  - User explicitly asks to search on ArXiv (e.g., "在ArXiv上搜索...", "查一下arxiv...")
  - User asks for daily AI paper summaries (e.g., "今天的AI论文摘要")
  
  DO NOT USE THIS SKILL WHEN:
  - User asks about a specific person's papers (e.g., "有没有钟鑫涛的文章", "张三发表了什么论文")
  - User asks about internal/research group documents (e.g., "我们组的论文", "课题组的文章")
  - User asks about papers that may exist locally WITHOUT time-sensitive keywords (e.g., plain "有没有关于遥感图像融合的文章" without "最新"/"latest")
  - The question is clearly about internal/local resources only
  
  KEY RULE: If the user says "最新" (latest), "最近" (recent), or similar time-sensitive keywords, this is NOT a local KB query — use this skill.
---

# ArXiv Watcher

This skill interacts with the ArXiv API to find and summarize the latest research papers.

## Capabilities

- **Search**: Find papers by keyword, author, or category.
- **Summarize**: Fetch the abstract and provide a concise summary.
- **Save to Memory**: Automatically record summarized papers to `memory/RESEARCH_LOG.md` for long-term tracking.
- **Deep Dive**: Use `web_fetch` on the PDF link to extract more details if requested.

## Workflow

1. Use `scripts/search_arxiv.sh "<query>"` to get the XML results.
2. Parse the XML (look for `<entry>`, `<title>`, `<summary>`, and `<link title="pdf">`).
3. Present the findings to the user.
4. **MANDATORY**: Append the title, authors, date, and summary of any paper discussed to `memory/RESEARCH_LOG.md`. Use the format:
   ```markdown
   ### [YYYY-MM-DD] TITLE_OF_PAPER
   - **Authors**: Author List
   - **Link**: ArXiv Link
   - **Summary**: Brief summary of the paper and its relevance.
   ```

## Examples

- "Busca los últimos papers sobre LLM reasoning en ArXiv."
- "Dime de qué trata el paper con ID 2512.08769."
- "Hazme un resumen de las novedades de hoy en ArXiv sobre agentes."

## Resources

- `scripts/search_arxiv.sh`: Direct API access script.
