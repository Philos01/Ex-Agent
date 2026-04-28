"""
API v1 routes - Core endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import List, Optional
import os
import sys
import json
import subprocess
import datetime
import shutil
import logging

from app.core.config import load_config, save_config, ensure_data_dirs, UPLOAD_DIR, METADATA_PATH, get_complete_config
from app.core.dependencies import get_db, get_current_user
from app.services.ingest import ingest_file
from app.utils.file_utils import save_upload, list_uploaded_files, delete_uploaded_file
from app.services.qa import answer_question, stream_answer
from app.services.vector_store import get_collection_info, reset_collection, clear_all
from app.services.embedding import get_recommended_models, EmbeddingService
from app.services.audit import log_action
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["core"])
logger = logging.getLogger(__name__)


class QARequest(BaseModel):
    question: str
    top_k: int = 5
    temperature: float = None
    top_p: float = None
    max_tokens: int = None
    presence_penalty: float = None
    frequency_penalty: float = None
    enable_thinking: bool = None
    use_react: bool = None
    provider: str = None
    messages: List[dict] = []


class ConfigRequest(BaseModel):
    config: dict


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int
    comment: Optional[str] = None


@router.get("/config")
def get_config():
    cfg = load_config()
    return {"config": cfg}


@router.post("/config")
def update_config(req: ConfigRequest):
    save_config(req.config)
    return {"success": True}


@router.get("/documents")
def list_documents():
    files = list_uploaded_files()
    return {"files": files}


@router.get("/documents/{filename}")
def get_document_info(filename: str):
    files = list_uploaded_files()
    for f in files:
        if f.get("filename") == filename:
            return f
    raise HTTPException(status_code=404, detail="Document not found")


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    cfg = get_complete_config()
    ensure_data_dirs()
    max_size = cfg.get("upload_max_size", 104857600)
    saved = []
    failed = []

    for f in files:
        file_ext = os.path.splitext(f.filename)[1].lower()
        temp_path = None
        processed_filename = None
        final_file_path = None
        added_to_metadata = False
        added_to_vector_store = False

        try:
            content = await f.read()
            if len(content) > max_size:
                failed.append({"filename": f.filename, "reason": f"文件大小超过限制 ({max_size // 1048576}MB)"})
                continue
            await f.seek(0)

            if file_ext in [".pdf", ".docx", ".doc"]:
                if file_ext == ".pdf" and not cfg.get("allow_pdf_conversion", False):
                    logger.debug("PDF 转换功能未启用，直接上传 PDF 文件: %s", f.filename)
                    dest = await save_upload(f)
                    processed_filename = os.path.basename(dest)
                    final_file_path = dest

                    file_size = os.path.getsize(dest)
                    metas = []
                    try:
                        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                    metas = [m for m in metas if m.get("filename") != processed_filename]
                    metas.append({
                        "filename": processed_filename,
                        "upload_time": datetime.datetime.utcnow().isoformat(),
                        "size": file_size,
                        "doc_type": file_ext,
                    })
                    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                    added_to_metadata = True

                    ingest_result = ingest_file(dest, provider=cfg.get("provider", "openai"))
                    added_to_vector_store = ingest_result.get("success", False)

                    saved.append({
                        "filename": processed_filename,
                        "chunks_count": ingest_result.get("chunks_count", 0),
                        "summary_generated": ingest_result.get("summary_generated", False)
                    })
                    logger.debug("PDF 文件 %s 直接上传成功", f.filename)
                    continue

                temp_path = await save_upload(f)
                logger.debug("处理文件: %s", temp_path)

                if file_ext == ".pdf":
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "scripts", "pdf2markdown.py")
                else:
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "scripts", "docx2markdown.py")

                temp_output_dir = os.path.join(os.path.dirname(temp_path), "convert_temp")
                os.makedirs(temp_output_dir, exist_ok=True)

                logger.debug("运行转换脚本: %s", script_path)
                python_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "..", ".venv", "Scripts", "python.exe")
                if not os.path.exists(python_exe):
                    python_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "..", ".venv", "bin", "python")
                if not os.path.exists(python_exe):
                    python_exe = sys.executable

                result = subprocess.run(
                    [python_exe, script_path, temp_path, temp_output_dir],
                    timeout=cfg.get("timeouts", {}).get("docx2markdown_subprocess", 300)
                )

                logger.debug("转换完成，返回码: %s", result.returncode)

                base_name = os.path.splitext(os.path.basename(temp_path))[0]
                md_files = []
                if os.path.exists(temp_output_dir):
                    for file in os.listdir(temp_output_dir):
                        if file.endswith(".md"):
                            md_files.append(os.path.join(temp_output_dir, file))

                if not md_files:
                    alt_output_dir = os.path.join(os.path.dirname(temp_path), "output")
                    if os.path.exists(alt_output_dir):
                        for file in os.listdir(alt_output_dir):
                            if file.endswith(".md"):
                                md_files.append(os.path.join(alt_output_dir, file))

                md_file = md_files[0] if md_files else None

                if md_file and os.path.exists(md_file):
                    final_md_name = f"{base_name}.md"
                    final_md_path = os.path.join(str(UPLOAD_DIR), final_md_name)
                    shutil.move(md_file, final_md_path)
                    processed_filename = final_md_name
                    final_file_path = final_md_path

                    delete_uploaded_file(os.path.basename(temp_path))
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    file_size = os.path.getsize(final_md_path)
                    metas = []
                    try:
                        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                    metas = [m for m in metas if m.get("filename") != processed_filename]
                    metas.append({
                        "filename": processed_filename,
                        "upload_time": datetime.datetime.utcnow().isoformat(),
                        "size": file_size,
                        "doc_type": ".md",
                        "original_type": file_ext,
                    })
                    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                    added_to_metadata = True

                    ingest_result = ingest_file(final_md_path, provider=cfg.get("provider", "openai"))
                    added_to_vector_store = ingest_result.get("success", False)

                    saved.append({
                        "filename": processed_filename,
                        "chunks_count": ingest_result.get("chunks_count", 0),
                        "summary_generated": ingest_result.get("summary_generated", False)
                    })
                    logger.debug("文件 %s 处理成功", f.filename)

                    if os.path.exists(temp_output_dir):
                        shutil.rmtree(temp_output_dir, ignore_errors=True)

                else:
                    raise Exception("转换失败：未找到输出的Markdown文件")

            elif file_ext in [".md", ".txt"]:
                dest = await save_upload(f)
                processed_filename = os.path.basename(dest)
                final_file_path = dest

                file_size = os.path.getsize(dest)
                metas = []
                try:
                    metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                except Exception:
                    pass
                metas = [m for m in metas if m.get("filename") != processed_filename]
                metas.append({
                    "filename": processed_filename,
                    "upload_time": datetime.datetime.utcnow().isoformat(),
                    "size": file_size,
                    "doc_type": file_ext,
                })
                METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                added_to_metadata = True

                ingest_result = ingest_file(dest, provider=cfg.get("provider", "openai"))
                added_to_vector_store = ingest_result.get("success", False)

                saved.append({
                    "filename": processed_filename,
                    "chunks_count": ingest_result.get("chunks_count", 0),
                    "summary_generated": ingest_result.get("summary_generated", False)
                })

            elif file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                logger.debug("跳过图片文件: %s", f.filename)
                failed.append({"filename": f.filename, "reason": "不支持图片文件"})
                continue

            else:
                logger.debug("跳过不支持的文件类型: %s", f.filename)
                failed.append({"filename": f.filename, "reason": f"不支持的文件类型: {file_ext}"})
                continue

        except Exception as e:
            logger.error("文件 %s 处理失败: %s", f.filename, e)
            import traceback
            traceback.print_exc()

            try:
                if added_to_vector_store and processed_filename:
                    try:
                        from app.services.vector_store import delete_documents_by_filename
                        deleted_count = delete_documents_by_filename(processed_filename)
                        logger.debug("已回滚，从向量库删除 %d 个文档", deleted_count)
                    except Exception as rollback_error:
                        logger.error("回滚向量库失败: %s", rollback_error)

                if processed_filename:
                    try:
                        from app.services.summary_store import delete_document_summary
                        delete_document_summary(processed_filename)
                        logger.debug("已删除文档摘要: %s", processed_filename)
                    except Exception as rollback_error:
                        logger.error("删除摘要失败: %s", rollback_error)

                if added_to_metadata and processed_filename:
                    try:
                        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                        metas = [m for m in metas if m.get("filename") != processed_filename]
                        METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                        logger.debug("已从 metadata 删除: %s", processed_filename)
                    except Exception as rollback_error:
                        logger.error("回滚 metadata 失败: %s", rollback_error)

                if final_file_path and os.path.exists(final_file_path):
                    try:
                        delete_uploaded_file(processed_filename)
                        os.remove(final_file_path)
                        logger.debug("已删除文件: %s", final_file_path)
                    except Exception as rollback_error:
                        logger.error("删除文件失败: %s", rollback_error)

                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            except Exception as full_rollback_error:
                logger.error("完整回滚过程出错: %s", full_rollback_error)
                import traceback
                traceback.print_exc()

            failed.append({"filename": f.filename, "reason": str(e)})

    return {"saved": saved, "failed": failed}


@router.delete("/documents/{filename}")
def delete_document(filename: str):
    target_filename = filename
    logger.debug("删除文档: %s", target_filename)

    try:
        from app.services.vector_store import delete_documents_by_filename
        deleted_count = delete_documents_by_filename(target_filename)
        logger.debug("已从向量库删除 %d 个文档片段", deleted_count)
    except Exception as e:
        logger.debug("从向量库删除文档失败: %s", e)

    try:
        from app.services.summary_store import delete_document_summary
        delete_document_summary(target_filename)
        logger.debug("已删除文档摘要: %s", target_filename)
    except Exception as e:
        logger.debug("删除文档摘要失败: %s", e)

    delete_uploaded_file(target_filename)

    return {"success": True, "deleted": target_filename}


@router.get("/stats")
def get_stats():
    info = get_collection_info()
    return {"vector_store": info}


@router.post("/reset")
def reset_knowledge_base():
    clear_all()
    return {"success": True}


@router.post("/qa")
async def qa_endpoint(req: QARequest):
    cfg = get_complete_config()
    provider = req.provider if req.provider else cfg.get("provider", "openai")

    logger.debug("Received QA request with params:")
    logger.debug("  question: %s...", req.question[:50])
    logger.debug("  top_k: %s", req.top_k)
    logger.debug("  temperature: %s", req.temperature)
    logger.debug("  top_p: %s", req.top_p)
    logger.debug("  max_tokens: %s", req.max_tokens)
    logger.debug("  presence_penalty: %s", req.presence_penalty)
    logger.debug("  frequency_penalty: %s", req.frequency_penalty)
    logger.debug("  enable_thinking: %s", req.enable_thinking)
    logger.debug("  messages history: %d messages", len(req.messages))

    import re
    skill_command_match = re.match(r'^/skill\s+(\S+)(?:\s+(.*))?$', req.question.strip())

    from app.skills import get_skill_manager
    skill_manager = get_skill_manager()

    if skill_command_match:
        skill_name = skill_command_match.group(1)
        raw_params = skill_command_match.group(2) or ""
        skill_params = {}
        if raw_params:
            for pair in raw_params.split():
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    skill_params[k.strip()] = v.strip()
                else:
                    skill_params.setdefault("query", pair)

        available_skills = [s["name"] for s in skill_manager.list_skills()]
        if skill_name in available_skills:
            use_skill = True
            logger.debug("Command-triggered skill: %s, params: %s", skill_name, skill_params)
        else:
            use_skill = False
            skill_name = None
            skill_params = None
            logger.debug("Skill '%s' not found, falling back to RAG", skill_name)
    else:
        use_skill, skill_name, skill_params = skill_manager.should_use_skill(req.question, provider=provider)

    docs = []
    sources = []

    if not use_skill:
        from app.services.qa import _retrieve_documents
        docs = _retrieve_documents(req.question, provider=provider, top_k=req.top_k)
        sources = [d.get("metadata", {}) for d in docs]

    generation_params = {
        "top_k": req.top_k,
        "temperature": req.temperature,
        "top_p": req.top_p,
        "max_tokens": req.max_tokens,
        "presence_penalty": req.presence_penalty,
        "frequency_penalty": req.frequency_penalty,
        "enable_thinking": req.enable_thinking,
        "use_react": req.use_react,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "use_skill": use_skill,
        "skill_name": skill_name,
        "skill_params": skill_params,
    }

    async def generate():
        async for chunk in stream_answer(
            req.question,
            provider=provider,
            include_state=True,
            **generation_params
        ):
            if chunk.get("type") == "token":
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            elif chunk.get("type") == "state":
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            elif chunk.get("type") == "sources":
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            elif chunk.get("type") == "skill_result":
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            elif chunk.get("type") == "done":
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/qa/sync")
def qa_sync_endpoint(req: QARequest):
    cfg = get_complete_config()
    provider = req.provider if req.provider else cfg.get("provider", "openai")

    result = answer_question(
        req.question,
        provider=provider,
        top_k=req.top_k,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        presence_penalty=req.presence_penalty,
        frequency_penalty=req.frequency_penalty,
        enable_thinking=req.enable_thinking,
        use_react=req.use_react,
        messages=[{"role": m.role, "content": m.content} for m in req.messages]
    )

    return result


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    logger.info("Received feedback for message %s: rating=%d, comment=%s", req.message_id, req.rating, req.comment)
    return {"success": True, "message_id": req.message_id}


@router.get("/embedding/models")
def get_embedding_models():
    models = get_recommended_models()
    return {"models": models}


@router.get("/documents/{filename}/chunks")
def get_document_chunks(filename: str):
    from app.services.vector_store import get_collection
    collection = get_collection()

    all_docs = collection.get(include=["documents", "metadatas"])

    chunks = []
    for i, (doc, meta) in enumerate(zip(all_docs.get("documents", []), all_docs.get("metadatas", []))):
        if meta and meta.get("source") == filename:
            chunks.append({
                "index": meta.get("chunk_index", i),
                "text": doc[:500] + "..." if len(doc) > 500 else doc,
                "full_text": doc,
                "metadata": meta
            })

    chunks.sort(key=lambda x: x.get("index", 0))

    return {
        "filename": filename,
        "chunks": chunks,
        "total_chunks": len(chunks)
    }
