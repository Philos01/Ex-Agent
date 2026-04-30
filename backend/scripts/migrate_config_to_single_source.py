"""
Migration script: Merge DEFAULT_CONFIG into config.json, then clean up config.py.

Run this script ONCE, then config.json becomes the single source of truth.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.json"
BACKUP_PATH = ROOT / "config.json.backup"


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def main():
    DEFAULT_CONFIG = {
        "provider": "openai",
        "embedding_mode": "local",
        "local_embedding_model": "BAAI/bge-small-zh-v1.5",
        "local_model_cache_dir": "",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_embedding_model": "text-embedding-3-small",
        "openai_chat_model": "gpt-3.5-turbo",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "",
        "chunk_size": 1500,
        "chunk_overlap": 225,
        "temperature": 0.7,
        "top_k": 5,
        "top_p": 0.9,
        "max_tokens": 2048,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "max_history": 10,
        "upload_max_size": 104857600,
        "allow_user_registration": False,
        "allow_pdf_conversion": False,
        "pdf_conversion_method": "marker",
        "hybrid_search": {
            "enabled": True,
            "initial_retrieve_count": 20,
            "final_select_count": 5,
            "bm25_weight": 0.5,
            "embedding_weight": 0.5,
            "rerank_model": "BAAI/bge-reranker-v2-m3",
            "enable_query_rewrite": True
        },
        "summary_search": {
            "enabled": True,
            "relevance_threshold": 0.6,
            "summary_top_k": 5,
            "content_top_k": 3,
            "auto_generate_summary": True,
            "enable_query_rewrite": True
        },
        "context_management": {
            "enabled": True,
            "max_history_rounds": 5,
            "exclude_error_messages": True,
            "exclude_questionable_messages": False
        },
        "timeouts": {
            "enabled": True,
            "requests_post": 60,
            "requests_stream": 60,
            "document_summary": 300,
            "skill_executor_python": 60,
            "skill_executor_shell": 60,
            "react_agent_subprocess": 60,
            "docx2markdown_subprocess": 300,
            "pdf_conversion_subprocess": 1800
        },
        "parent_document_retrieval": {
            "enabled": False,
            "parent_max_chars": 8000,
            "parent_min_chars": 300,
            "parent_max_count": 5,
            "child_chunk_size": 300,
            "child_chunk_overlap": 60,
            "child_retrieve_count": 20,
            "parent_max_chars_total": 12000,
            "enable_distance_scoring": True,
            "fallback_to_hybrid": True
        },
        "skills": {
            "enabled": True,
            "auto_discover": True,
            "arxiv-watcher": {
                "enabled": True,
                "version": "1.0.0"
            },
            "amap-weather": {
                "enabled": True,
                "version": "1.0.0"
            },
            "arxiv_search": {
                "enabled": True,
                "max_results": 5
            }
        }
    }

    print(f"配置文件路径: {CONFIG_PATH}")
    print(f"备份路径: {BACKUP_PATH}")

    if CONFIG_PATH.exists():
        shutil.copy(CONFIG_PATH, BACKUP_PATH)
        print(f"已备份原 config.json -> {BACKUP_PATH}")
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            disk_cfg = json.load(f)
    else:
        print("config.json 不存在，将以 DEFAULT_CONFIG 为基础创建")
        disk_cfg = {}

    if "openai_api_key" in disk_cfg:
        del disk_cfg["openai_api_key"]

    merged = _deep_merge(DEFAULT_CONFIG, disk_cfg)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4, ensure_ascii=False)

    print(f"已合并写入 config.json")

    disk_cfg_keys = set(disk_cfg.keys()) if disk_cfg else set()
    default_keys = set(DEFAULT_CONFIG.keys())
    missing_in_disk = default_keys - disk_cfg_keys

    added_keys = default_keys - disk_cfg_keys

    if added_keys:
        print(f"\n[新增到 config.json 的顶层字段]: {sorted(added_keys)}")

    changed_subfields = []
    for section in ["hybrid_search", "summary_search", "context_management",
                     "timeouts", "parent_document_retrieval", "skills"]:
        if section in disk_cfg and section in DEFAULT_CONFIG:
            disk_keys = set(disk_cfg[section].keys())
            default_keys_s = set(DEFAULT_CONFIG[section].keys())
            added_in_section = default_keys_s - disk_keys
            if added_in_section:
                changed_subfields.append(f"  {section}: {sorted(added_in_section)}")

    if changed_subfields:
        print(f"[新增到 config.json 的子字段]:\n" + "\n".join(changed_subfields))

    print("\n迁移完成！config.json 现在包含 DEFAULT_CONFIG 和原 config.json 的完整并集。")


if __name__ == "__main__":
    main()
