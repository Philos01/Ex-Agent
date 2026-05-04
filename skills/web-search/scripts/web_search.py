#!/usr/bin/env python3
"""
Web Search Skill - Multi-engine web search with history support.

Supports Google Custom Search, Bing Search, and DuckDuckGo (fallback).
Stores search history locally for user convenience.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: 'beautifulsoup4' library is required. Install with: pip install beautifulsoup4")
    sys.exit(1)

HISTORY_FILE = os.path.expanduser("~/.web_search_history.json")
MAX_HISTORY = 50


class SearchError(Exception):
    pass


class NetworkError(SearchError):
    pass


class RateLimitError(SearchError):
    pass


class APIKeyError(SearchError):
    pass


def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"searches": []}
    return {"searches": []}


def save_history(history: dict) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_to_history(query: str, result_count: int, engine: str) -> None:
    history = load_history()
    entry = {
        "id": str(uuid.uuid4()),
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "result_count": result_count,
        "engine": engine,
    }
    history["searches"].insert(0, entry)
    if len(history["searches"]) > MAX_HISTORY:
        history["searches"] = history["searches"][:MAX_HISTORY]
    save_history(history)


def show_history() -> None:
    history = load_history()
    if not history["searches"]:
        print("No search history found.")
        return
    print("\n📜 Search History:")
    print("-" * 60)
    for i, entry in enumerate(history["searches"], 1):
        timestamp = entry["timestamp"][:16].replace("T", " ")
        print(f"{i}. {entry['query']}")
        print(f"   [{timestamp}] | {entry['engine']} | {entry['result_count']} results")
    print("-" * 60)
    print(f"\nTotal: {len(history['searches'])} searches (max {MAX_HISTORY})")


def clear_history() -> None:
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        print("Search history cleared.")
    else:
        print("No history to clear.")


def search_google(query: str, num: int = 10, safe: bool = False) -> list[dict]:
    api_key = os.environ.get("GOOGLE_API_KEY")
    search_engine_id = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise APIKeyError("Google API key or Search Engine ID not configured")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": min(num, 10),
        "safe": "active" if safe else "off",
    }

    response = _make_request(url, params=params)

    if response.status_code == 429:
        raise RateLimitError("Google API rate limit exceeded")

    if response.status_code != 200:
        raise SearchError(f"Google API error: {response.status_code}")

    data = response.json()
    results = []
    for i, item in enumerate(data.get("items", []), 1):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source": "Google",
            "rank": i,
        })
    return results


def search_bing(query: str, num: int = 10, safe: bool = False) -> list[dict]:
    api_key = os.environ.get("BING_API_KEY")

    if not api_key:
        raise APIKeyError("Bing API key not configured")

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": min(num, 50),
        "safeSearch": "Moderate" if safe else "Off",
        "textDecorations": False,
        "textFormat": "Raw",
    }

    response = _make_request(url, headers=headers, params=params)

    if response.status_code == 429:
        raise RateLimitError("Bing API rate limit exceeded")

    if response.status_code != 200:
        raise SearchError(f"Bing API error: {response.status_code}")

    data = response.json()
    results = []
    for i, item in enumerate(data.get("webPages", {}).get("value", []), 1):
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
            "source": "Bing",
            "rank": i,
        })
    return results


def search_duckduckgo(query: str, num: int = 10) -> list[dict]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query}

    response = _make_request(url, params=params)

    if response.status_code != 200:
        raise SearchError(f"DuckDuckGo error: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for i, result in enumerate(soup.select(".result"), 1):
        if i > num:
            break

        title_elem = result.select_one(".result__title a")
        snippet_elem = result.select_one(".result__snippet")
        if title_elem:
            results.append({
                "title": title_elem.get_text(strip=True),
                "url": title_elem.get("href", ""),
                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                "source": "DuckDuckGo",
                "rank": i,
            })

    return results


def _make_request(url: str, headers: dict = None, params: dict = None, max_retries: int = 3) -> requests.Response:
    headers = headers or {}
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            return response
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise NetworkError("Request timeout after retries")
            time.sleep(2 ** attempt)
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise NetworkError("Network connection failed")
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {str(e)}")

    raise NetworkError("Max retries exceeded")


def search(query: str, engine: str = "auto", num: int = 10, safe: bool = False, json_output: bool = False) -> list[dict]:
    engines_priority = ["google", "bing", "duckduckgo"]

    if engine == "auto":
        available_engines = []
        if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_SEARCH_ENGINE_ID"):
            available_engines.append("google")
        if os.environ.get("BING_API_KEY"):
            available_engines.append("bing")
        available_engines.append("duckduckgo")
    else:
        available_engines = [engine]

    last_error = None
    for eng in available_engines:
        try:
            if eng == "google":
                return search_google(query, num, safe)
            elif eng == "bing":
                return search_bing(query, num, safe)
            elif eng == "duckduckgo":
                return search_duckduckgo(query, num)
        except RateLimitError:
            raise
        except APIKeyError:
            if eng != available_engines[-1]:
                continue
            raise
        except (NetworkError, SearchError) as e:
            last_error = e
            if eng != available_engines[-1]:
                continue
            raise NetworkError(f"All search engines failed. Last error: {last_error}")

    raise SearchError("No search engine available")


def format_results(results: list[dict], json_output: bool = False) -> str:
    if json_output:
        return json.dumps(results, ensure_ascii=False, indent=2)

    output = []
    output.append("\n" + "=" * 60)
    output.append(f"🔍 Search Results ({len(results)} found)")
    output.append("=" * 60 + "\n")

    for result in results:
        output.append(f"📌 {result['title']}")
        output.append(f"🔗 {result['url']}")
        output.append(f"📝 {result['snippet']}")
        output.append(f"   来源: {result['source']} | 排名: {result['rank']}")
        output.append("-" * 60)

    return "\n".join(output)


def handle_search_error(error: Exception) -> None:
    error_messages = {
        NetworkError: ("❌ 网络连接失败，请检查您的网络设置后重试。", 3),
        RateLimitError: ("⚠️ 搜索服务暂时限流，请稍后再试。", 0),
        APIKeyError: ("⚠️ 搜索服务配置错误，请检查API密钥设置。", 0),
        SearchError: ("❌ 搜索失败，请尝试其他关键词或稍后重试。", 0),
    }

    msg, retry = error_messages.get(type(error), ("❌ 发生未知错误，请重试。", 0))
    print(msg, file=sys.stderr)

    if retry > 0:
        print(f"将在 {retry} 秒后自动重试...", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Web Search Skill - Multi-engine search with history")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--engine", "-e", choices=["google", "bing", "duckduckgo", "auto"], default="auto", help="Search engine to use")
    parser.add_argument("--num", "-n", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    parser.add_argument("--safe", "-s", action="store_true", help="Enable safe search (filters adult content)")
    parser.add_argument("--history", action="store_true", help="Show search history")
    parser.add_argument("--rerun", metavar="QUERY", help="Re-run a past search")
    parser.add_argument("--clear-history", action="store_true", help="Clear all search history")
    parser.add_argument("--params", help="JSON parameters file (for skill system call)")

    args = parser.parse_args()

    # 处理 --params 参数（技能系统调用方式）
    is_skill_call = args.params is not None
    
    if args.params:
        try:
            with open(args.params, 'r', encoding='utf-8') as f:
                params = json.load(f)
            # 从 params 中提取参数
            query = params.get("query") or params.get("question")
            engine = params.get("engine", "auto")
            num = params.get("num", 10)
            safe = params.get("safe", False)
            json_output = True  # 技能调用总是输出 JSON
        except Exception as e:
            print(f"错误: 无法读取参数文件: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 常规命令行调用方式
        query = args.query
        engine = args.engine
        num = args.num
        safe = args.safe
        json_output = args.json

    if args.clear_history:
        clear_history()
        return

    if args.history:
        show_history()
        return

    if args.rerun:
        query = args.rerun
        engine = args.engine

    if not query:
        parser.print_help()
        return

    try:
        start_time = time.time()
        results = search(query, engine=engine, num=num, safe=safe)
        elapsed = time.time() - start_time

        add_to_history(query, len(results), engine)

        if json_output or is_skill_call:
            # 技能调用时，输出结构化的 JSON 结果
            result = {
                "success": True,
                "data": results
            }
            # 使用 ensure_ascii=True 来避免编码问题，在接收端解码
            print(json.dumps(result, ensure_ascii=True))
        else:
            print(format_results(results, False))
            print(f"\n✅ 共找到 {len(results)} 条结果 | 搜索耗时: {elapsed:.2f}秒")
            print("\n您可以输入以下命令：")
            print("- '查看搜索历史' - 查看最近的搜索记录")
            print("- '重新搜索 xxx' - 重新执行某个历史搜索")
            print("- '清除搜索历史' - 清除所有历史记录")

    except Exception as e:
        if is_skill_call or json_output:
            error_result = {
                "success": False,
                "error": str(e)
            }
            print(json.dumps(error_result, ensure_ascii=True))
        else:
            handle_search_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
