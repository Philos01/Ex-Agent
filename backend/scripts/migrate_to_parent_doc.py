import os
import sys
import json
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import load_config, save_config, UPLOAD_DIR, CHROMA_DIR
from app.services.parent_document import generate_parent_documents, generate_child_chunks
from app.services.parent_store import ParentDocumentStore
from app.services.vector_store import add_documents, delete_documents_by_filename, clear_all
from app.services.ingest import extract_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_all_documents(dry_run: bool = False):
    cfg = load_config()
    pdr_config = cfg.get("parent_document_retrieval", {})
    child_chunk_size = pdr_config.get("child_chunk_size", 300)
    child_chunk_overlap = pdr_config.get("child_chunk_overlap", 60)
    parent_max_chars = pdr_config.get("parent_max_chars", 8000)
    parent_min_chars = pdr_config.get("parent_min_chars", 300)

    if not UPLOAD_DIR.exists():
        logger.error(f"上传目录不存在: {UPLOAD_DIR}")
        return

    md_files = list(UPLOAD_DIR.glob("*.md")) + list(UPLOAD_DIR.glob("*.txt"))
    logger.info(f"找到 {len(md_files)} 个 Markdown/文本文件")

    if dry_run:
        for f in md_files:
            logger.info(f"[DRY RUN] 将处理: {f.name}")
        return

    parent_store = ParentDocumentStore()

    logger.info("清空向量库，准备重新摄入...")
    clear_all()

    total_parents = 0
    total_children = 0

    for filepath in md_files:
        filename = filepath.name
        logger.info(f"正在处理: {filename}")

        text = extract_text(str(filepath))
        if not text.strip():
            logger.warning(f"文件 {filename} 内容为空，跳过")
            continue

        parents = generate_parent_documents(
            text, filename,
            min_parent_chars=parent_min_chars,
            max_parent_chars=parent_max_chars
        )

        all_children = []
        for parent in parents:
            children = generate_child_chunks(
                parent,
                child_chunk_size=child_chunk_size,
                child_chunk_overlap=child_chunk_overlap
            )
            all_children.extend(children)

        parent_store.delete_by_filename(filename)
        parent_store.save_parents(parents)

        child_ids = [f"{c['parent_id']}_{c['chunk_index']}" for c in all_children]
        child_texts = [c['text'] for c in all_children]
        child_metas = [
            {
                "source": c['filename'],
                "chunk_index": c['chunk_index'],
                "parent_id": c['parent_id'],
                "section_title": c['section_title'],
                "chunk_type": "child",
                "ingest_time": "",
                "file_type": os.path.splitext(filename)[1].lower(),
            }
            for c in all_children
        ]

        if child_texts:
            add_documents(ids=child_ids, documents=child_texts, metadatas=child_metas)

        total_parents += len(parents)
        total_children += len(all_children)
        logger.info(f"完成: {filename} → {len(parents)} 父文档 + {len(all_children)} 子切片")

    cfg["parent_document_retrieval"]["enabled"] = True
    save_config(cfg)
    logger.info("已启用 parent_document_retrieval 配置")

    logger.info(f"迁移完成！总计: {total_parents} 父文档, {total_children} 子切片")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="迁移到父文档检索模式")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际执行")
    args = parser.parse_args()

    migrate_all_documents(dry_run=args.dry_run)
