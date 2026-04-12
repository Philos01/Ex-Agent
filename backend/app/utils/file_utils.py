"""
Helpers for saving and listing uploaded files and metadata
"""
import aiofiles
import os
import json
from pathlib import Path
from app.core.config import UPLOAD_DIR, METADATA_PATH, ensure_data_dirs
from fastapi import UploadFile
import datetime


async def save_upload(file: UploadFile) -> str:
    ensure_data_dirs()
    dest = UPLOAD_DIR / file.filename
    size = 0
    async with aiofiles.open(dest, "wb") as out:
        content = await file.read()
        await out.write(content)
        size = len(content)
    # update metadata - 先删除已存在的同名文件记录，再添加新记录
    metas = []
    try:
        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        metas = []
    # 过滤掉已存在的同名文件记录
    metas = [m for m in metas if m.get("filename") != file.filename]
    metas.append({
        "filename": file.filename,
        "upload_time": datetime.datetime.utcnow().isoformat(),
        "size": size,
        "doc_type": os.path.splitext(file.filename)[1].lower(),
    })
    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(dest)


def list_uploaded_files():
    ensure_data_dirs()
    try:
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def delete_uploaded_file(filename: str):
    ensure_data_dirs()
    path = UPLOAD_DIR / filename
    if path.exists():
        path.unlink()
    metas = list_uploaded_files()
    metas = [m for m in metas if m.get("filename") != filename]
    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 从向量库中删除对应的文档
    try:
        from app.services.vector_store import init_collection
        collection = init_collection()
        # 获取所有文档，然后过滤出source匹配的
        all_docs = collection.get(include=["metadatas"])
        if all_docs and all_docs.get("metadatas") and all_docs.get("ids"):
            # 过滤出source匹配的ids
            to_delete = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('source') == filename:
                    to_delete.append(all_docs['ids'][i])
            
            if to_delete:
                collection.delete(ids=to_delete)
                print(f"[DEBUG] Deleted {len(to_delete)} vectors for file: {filename}")
            else:
                print(f"[DEBUG] No vectors found for file: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to delete vectors for {filename}: {e}")
        import traceback
        traceback.print_exc()
