---
name: arxiv-watcher
description: |
  Search and summarize the latest academic papers from the external ArXiv database (arxiv.org).
  
  Use when: user asks for latest, newest, or recent research papers in any field. User wants time-sensitive academic searches that require real-time external data. User explicitly asks to search on ArXiv. User asks for daily/weekly paper summaries or trending research topics. User mentions keywords suggesting they need the most up-to-date published work that a local knowledge base cannot provide.
  
  Do NOT use when: user asks about specific authors' papers that may exist in local knowledge base. User asks about internal documents, research group papers, or materials already stored locally. User asks a general question about papers without indicating need for latest/external search. The question is clearly answerable from local resources without external search.
input_parameters:
  query:
    type: string
    required: true
    description: Search query string extracted from the user's question
  max_results:
    type: integer
    required: false
    default: 5
    description: Maximum number of papers to return
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
