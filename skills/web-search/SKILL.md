---
name: web-search
description: |
  Search the internet via search engine APIs (Google, Bing, DuckDuckGo) and return structured results.
  
  Use when: user asks to search the web or internet for general information, news, or online resources. User wants to find information that is not in the local knowledge base and is not academic papers (papers go to arxiv-watcher). User asks about current events, online tutorials, documentation, or general web content. User explicitly says "搜索", "search", "上网查", or similar web search phrases.
  
  Do NOT use when: user asks about internal documents or knowledge base content. User asks about academic papers or research literature (delegate to arxiv-watcher). User asks about weather (delegate to amap-weather). The question is answerable from local knowledge base without external search.
input_parameters:
  query:
    type: string
    required: true
    description: Search query string extracted from the user's question
  num_results:
    type: integer
    required: false
    default: 10
    description: Number of search results to return
---

# Web Search Skill

This skill performs web searches using search engine APIs and returns structured, organized results to users.

## Capabilities

- **Multi-Engine Search**: Supports Google, Bing, and DuckDuckGo as fallback
- **Structured Results**: Returns title, snippet/summary, URL, and source for each result
- **Search History**: Tracks recent searches, supports viewing and re-running past searches
- **Error Recovery**: Handles network failures, API rate limits, and invalid responses gracefully
- **Privacy Compliant**: Respects robots.txt where applicable and search engine Terms of Service

## Configuration

### Required Environment Variables

```bash
# At least one search API key is required
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

BING_API_KEY=your_bing_api_key

# DuckDuckGo (no API key required, uses HTML scraping)
# Requires: pip install beautifulsoup4 requests
```

### Installation

```bash
pip install requests beautifulsoup4
```

## Usage

### Basic Search

```bash
python3 scripts/web_search.py "search query"
```

### Search with Options

```bash
# Search with specific engine (google, bing, duckduckgo)
python3 scripts/web_search.py "machine learning" --engine bing

# Limit number of results (default: 10)
python3 scripts/web_search.py "Python tutorials" --num 5

# Output as JSON
python3 scripts/web_search.py "AI news" --json

# Search with safe mode (filters adult content)
python3 scripts/web_search.py "programming" --safe
```

### Search History Commands

```bash
# View search history
python3 scripts/web_search.py --history

# Re-run a past search
python3 scripts/web_search.py --rerun "past search query"

# Clear search history
python3 scripts/web_search.py --clear-history
```

## Search Result Format

Each search result contains:

| Field | Description |
|-------|-------------|
| `title` | Page title |
| `url` | Direct URL to the page |
| `snippet` | Brief summary/description of the page content |
| `source` | Search engine that returned this result |
| `rank` | Position in search results (1-indexed) |

## Error Handling

| Error Type | User Message | Recovery Action |
|------------|--------------|-----------------|
| Network Failure | "网络连接失败，请检查您的网络设置" | Retry up to 3 times with exponential backoff |
| API Rate Limit | "搜索服务暂时限流，请稍后再试" | Switch to alternative engine or wait |
| Invalid API Key | "搜索服务配置错误，请检查API密钥" | Prompt user to configure valid keys |
| No Results | "未找到相关结果，请尝试其他关键词" | Suggest alternative queries |
| Timeout | "搜索请求超时，请重试" | Retry once, then suggest alternative |

## Search History Storage

Search history is stored in `~/.web_search_history.json` with the following structure:

```json
{
  "searches": [
    {
      "id": "uuid",
      "query": "search query",
      "timestamp": "2026-05-01T12:00:00Z",
      "result_count": 10,
      "engine": "bing"
    }
  ]
}
```

History is limited to 50 recent searches. Older entries are automatically pruned.

## Legal Compliance & Privacy

### Search Engine Terms of Service

- **Google Custom Search**: Requires valid API key, subject to Google Terms of Service
- **Bing Search**: Subject to Microsoft/Bing Terms of Service and Acceptable Use Policy
- **DuckDuckGo**: For non-commercial use; respects Do Not Track headers

### User Privacy

- Search queries are NOT logged to external services beyond necessary API calls
- Search history is stored locally only in `~/.web_search_history.json`
- No personal identification information is transmitted with search requests
- Users can clear their search history at any time with `--clear-history`

### Rate Limits & Best Practices

- Respect rate limits of each search API provider
- Implement caching when possible to reduce redundant API calls
- Do not bundle multiple queries into single API calls unless explicitly supported

## Example Interaction Flow

```
User: 帮我搜索一下关于量子计算的最新进展
Assistant: [Invokes web-search skill]

Processing search: 量子计算 最新进展
Using search engine: Bing
Found 10 results

---

🔍 量子计算最新研究进展 (2026)
📎 https://example-quantum-news.com/research
📝 总结了2026年量子计算领域的重大突破，包括...
来源: Bing

🔍 IBM Quantum System Two: Next Generation Quantum Computer
📎 https://ibm.com/quantum/system-two
📝 IBM发布了新一代量子计算系统，配备超过1000量子比特...
来源: Google

...

---
📚 共找到 10 条结果 | 搜索耗时: 0.32秒

您可以输入以下命令：
- "查看搜索历史" - 查看最近的搜索记录
- "重新搜索 xxx" - 重新执行某个历史搜索
- "清除搜索历史" - 清除所有历史记录
```

## Scripts

- `scripts/web_search.py`: Main search script with all functionality
