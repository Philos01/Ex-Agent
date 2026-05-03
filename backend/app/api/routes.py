from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import FileResponse
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

router = APIRouter(tags=["api"])
logger = logging.getLogger(__name__)


def _format_conversation_history_for_skill(messages: list) -> str:
    """Format recent messages as context for skill selection."""
    if not messages:
        return ""
    recent = messages[-6:]
    lines = []
    for msg in recent:
        role = msg.get("role", "user") if isinstance(msg, dict) else getattr(msg, "role", "user")
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}: {content[:200]}")
    return "\n".join(lines)


class Message(BaseModel):
    role: str  # "user" 或 "assistant"
    content: str
    skill_result: Optional[str] = None  # 技能执行结果（用于上下文）
    skill_name: Optional[str] = None  # 使用的技能名称


class QARequest(BaseModel):
    question: str
    top_k: int = 5
    provider: str = None
    stream: bool = False
    temperature: float = None
    top_p: float = None
    max_tokens: int = None
    presence_penalty: float = None
    frequency_penalty: float = None
    enable_thinking: bool = None  # 是否启用思考阶段
    reasoning_effort: Optional[str] = None  # 思考强度
    use_react: bool = None  # 是否启用 ReAct 多步推理模式
    use_graph: bool = None  # 是否启用图结构检索
    messages: List[Message] = []  # 对话历史


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
            # 检查文件类型
            if file_ext in [".pdf", ".docx", ".doc", ".xlsx", ".xls"]:
                # 对于 PDF 文件，如果转换功能未启用，则直接上传
                if file_ext == ".pdf" and not cfg.get("allow_pdf_conversion", False):
                    logger.debug("PDF conversion disabled, uploading raw PDF: %s", f.filename)
                    dest = await save_upload(f)
                    processed_filename = os.path.basename(dest)
                    final_file_path = dest
                    
                    # 先添加到 metadata
                    file_size = os.path.getsize(dest)
                    metas = []
                    try:
                        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                    # 过滤掉已存在的同名文件记录
                    metas = [m for m in metas if m.get("filename") != processed_filename]
                    metas.append({
                        "filename": processed_filename,
                        "upload_time": datetime.datetime.utcnow().isoformat(),
                        "size": file_size,
                        "doc_type": file_ext,
                    })
                    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                    added_to_metadata = True
                    
                    # 处理文件到知识库
                    ingest_result = ingest_file(dest, provider=cfg.get("provider", "openai"))
                    added_to_vector_store = ingest_result.get("success", False)
                    
                    saved.append({
                        "filename": processed_filename,
                        "chunks_count": ingest_result.get("chunks_count", 0),
                        "summary_generated": ingest_result.get("summary_generated", False)
                    })
                    logger.debug("PDF 文件 %s 直接上传成功", f.filename)
                    continue
                
                # 1. 先保存文件到临时位置
                temp_path = await save_upload(f)
                logger.debug("处理文件: %s", temp_path)
                
                # 2. 根据文件类型选择转换脚本
                if file_ext == ".pdf":
                    pdf_conversion_method = cfg.get("pdf_conversion_method", "marker")
                    if pdf_conversion_method == "markitdown":
                        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "pdf2markdown_markitdown.py")
                        logger.debug("使用 MarkItDown 进行 PDF 转换")
                    else:
                        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "pdf2markdown.py")
                        logger.debug("使用 Marker 进行 PDF 转换")
                elif file_ext in [".xlsx", ".xls"]:
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "excel2markdown.py")
                else:
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "docx2markdown.py")
                
                # 使用专门的临时输出目录
                temp_output_dir = os.path.join(os.path.dirname(temp_path), "convert_temp")
                os.makedirs(temp_output_dir, exist_ok=True)
                
                logger.debug("运行转换脚本: %s", script_path)
                python_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", ".venv", "Scripts", "python.exe")
                if not os.path.exists(python_exe):
                    python_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", ".venv", "bin", "python")
                if not os.path.exists(python_exe):
                    python_exe = sys.executable
                
                # 根据文件类型选择超时
                if file_ext == ".pdf":
                    timeout_sec = cfg.get("timeouts", {}).get("pdf_conversion_subprocess", 1800)
                else:
                    timeout_sec = cfg.get("timeouts", {}).get("docx2markdown_subprocess", 300)

                # 运行转换脚本（输出直接显示在终端，便于调试）
                result = subprocess.run(
                    [python_exe, script_path, temp_path, temp_output_dir],
                    timeout=timeout_sec
                )
                
                logger.debug("转换完成，返回码: %s", result.returncode)
                
                # 3. 查找转换后的Markdown文件
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
                    # 4. 将Markdown文件移动到正式目录
                    final_md_name = f"{base_name}.md"
                    final_md_path = os.path.join(str(UPLOAD_DIR), final_md_name)
                    shutil.move(md_file, final_md_path)
                    processed_filename = final_md_name
                    final_file_path = final_md_path
                    
                    # 5. 更新元数据 - 先删除临时文件，再添加正式文件
                    delete_uploaded_file(os.path.basename(temp_path))
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    md_size = os.path.getsize(final_md_path)
                    metas = []
                    try:
                        metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                    # 过滤掉已存在的同名文件记录
                    metas = [m for m in metas if m.get("filename") != final_md_name]
                    metas.append({
                        "filename": final_md_name,
                        "upload_time": datetime.datetime.utcnow().isoformat(),
                        "size": md_size,
                        "doc_type": ".md",
                    })
                    METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                    added_to_metadata = True
                    
                    # 6. 加入知识库
                    ingest_result = ingest_file(final_md_path, provider=cfg.get("provider", "openai"))
                    added_to_vector_store = ingest_result.get("success", False)
                    
                    saved.append({
                        "filename": final_md_name,
                        "chunks_count": ingest_result.get("chunks_count", 0),
                        "summary_generated": ingest_result.get("summary_generated", False)
                    })
                    logger.debug("文件 %s 处理成功", f.filename)
                    
                    # 清理临时目录
                    if os.path.exists(temp_output_dir):
                        shutil.rmtree(temp_output_dir, ignore_errors=True)
                    alt_output_dir = os.path.join(os.path.dirname(temp_path), "output")
                    if os.path.exists(alt_output_dir):
                        shutil.rmtree(alt_output_dir, ignore_errors=True)
                else:
                    raise Exception("转换失败，未生成Markdown文件")
            
            # 过滤掉图片文件
            elif file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                logger.debug("跳过图片文件: %s", f.filename)
                failed.append({"filename": f.filename, "reason": "不支持图片文件"})
                continue
            
            # 处理其他文件类型
            else:
                dest = await save_upload(f)
                processed_filename = os.path.basename(dest)
                final_file_path = dest
                
                # 添加到 metadata
                file_size = os.path.getsize(dest)
                metas = []
                try:
                    metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                except Exception:
                    pass
                # 过滤掉已存在的同名文件记录
                metas = [m for m in metas if m.get("filename") != processed_filename]
                metas.append({
                    "filename": processed_filename,
                    "upload_time": datetime.datetime.utcnow().isoformat(),
                    "size": file_size,
                    "doc_type": file_ext,
                })
                METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                added_to_metadata = True
                
                # 处理文件到知识库
                ingest_result = ingest_file(dest, provider=cfg.get("provider", "openai"))
                added_to_vector_store = ingest_result.get("success", False)
                
                saved.append({
                    "filename": processed_filename,
                    "chunks_count": ingest_result.get("chunks_count", 0),
                    "summary_generated": ingest_result.get("summary_generated", False)
                })
                logger.debug("文件 %s 处理成功", f.filename)
        except Exception as e:
            logger.error("文件 %s 处理失败: %s", f.filename, e, exc_info=True)

            # 完整回滚
            try:
                # 1. 从向量库删除已添加的文档
                if added_to_vector_store and processed_filename:
                    try:
                        from app.services.vector_store import delete_documents_by_filename
                        deleted_count = delete_documents_by_filename(processed_filename)
                        logger.debug("Rollback: deleted %d docs from vector store", deleted_count)
                    except Exception as rollback_error:
                        logger.error("Rollback vector store failed: %s", rollback_error)
                
                # 2. 删除对应的摘要
                if processed_filename:
                    try:
                        from app.services.summary_store import delete_document_summary
                        delete_document_summary(processed_filename)
                        logger.debug("Rollback: deleted summary for %s", processed_filename)
                    except Exception as rollback_error:
                        logger.error("Rollback summary delete failed: %s", rollback_error)
                
                # 3. 从 metadata 中删除
                if added_to_metadata and processed_filename:
                    try:
                        metas = []
                        try:
                            metas = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                        # 过滤掉该文件的记录
                        metas = [m for m in metas if m.get("filename") != processed_filename]
                        METADATA_PATH.write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
                        logger.debug("Rollback: removed %s from metadata", processed_filename)
                    except Exception as rollback_error:
                        logger.error("Rollback metadata failed: %s", rollback_error)
                
                # 4. 删除文件
                if final_file_path and os.path.exists(final_file_path):
                    try:
                        delete_uploaded_file(processed_filename)
                        os.remove(final_file_path)
                        logger.debug("Rollback: deleted file %s", final_file_path)
                    except Exception as rollback_error:
                        logger.error("Rollback file delete failed: %s", rollback_error)
                
                # 5. 清理临时文件
                if temp_path and os.path.exists(temp_path):
                    try:
                        delete_uploaded_file(os.path.basename(temp_path))
                        os.remove(temp_path)
                    except:
                        pass
                        
            except Exception as full_rollback_error:
                logger.error("Full rollback failed: %s", full_rollback_error, exc_info=True)
            
            failed.append({
                "filename": f.filename,
                "reason": str(e)
            })
            
            # 继续处理下一个文件，不中断整个流程
            continue
    
    # 自动更新知识图谱可视化（如果有成功处理的文件）
    graph_updated = False
    if saved:
        try:
            from app.services.graph_analysis import GraphAnalyzer
            analyzer = GraphAnalyzer()
            analyzer.visualize(output_path="data/knowledge_graph.html")
            graph_updated = True
            logger.info("知识图谱可视化已自动更新")
        except Exception as e:
            logger.warning("自动更新知识图谱可视化失败（非致命）: %s", e)
    
    # 返回结果，包含成功和失败的信息
    return {
        "status": "ok",
        "files": saved,
        "failed": failed,
        "graph_updated": graph_updated,
        "message": f"成功处理 {len(saved)} 个文件，失败 {len(failed)} 个文件"
    }


@router.get("/documents")
def get_documents():
    docs = list_uploaded_files()
    return {"documents": docs}


@router.delete("/documents/{filename:path}")
@router.delete("/documents")
def delete_document(filename: str = None, file: str = None):
    """删除文档，支持路径参数和查询参数两种方式"""
    # 优先使用查询参数
    target_filename = file or filename
    if not target_filename:
        raise HTTPException(status_code=400, detail="请提供文件名")
    
    logger.debug("删除文档: %s", target_filename)
    
    # 从向量库删除对应的文档 chunks
    try:
        from app.services.vector_store import delete_documents_by_filename
        deleted_count = delete_documents_by_filename(target_filename)
        logger.debug("已从向量库删除 %d 个文档片段", deleted_count)
    except Exception as e:
        logger.debug("从向量库删除文档失败: %s", e)
    
    # 删除对应的摘要
    try:
        from app.services.summary_store import delete_document_summary
        delete_document_summary(target_filename)
        logger.debug("已删除文档摘要: %s", target_filename)
    except Exception as e:
        logger.debug("删除文档摘要失败: %s", e)
    
    delete_uploaded_file(target_filename)
    return {"status": "deleted", "file": target_filename}


@router.post("/clear")
def clear_knowledge():
    from app.services.vector_store import clear_all

    clear_all()
    return {"status": "cleared"}


@router.get("/config")
def get_config(current_user: User = Depends(get_current_user)):
    """
    Get system configuration (requires authentication)
    Never returns sensitive credentials like API keys
    """
    # load_config() already ensures API keys are not included
    return load_config()


@router.post("/config")
def post_config(
    data: dict, 
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update system configuration (admin only)
    Never saves sensitive credentials like API keys
    """
    # Check if user is admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only Administrators can modify system configuration"
        )
    
    cfg = load_config()
    
    # Get client info for audit log
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log each config change
    for key, value in data.items():
        old_value = cfg.get(key)
        if old_value != value:
            log_action(
                db=db,
                user=current_user,
                action="config_change",
                resource_type="system_config",
                resource_id=key,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(value) if value is not None else None,
                ip_address=client_host,
                user_agent=user_agent
            )
    
    cfg.update(data)
    save_config(cfg)
    return {"status": "saved", "config": cfg}


@router.get("/vector-store/status")
def get_vector_store_status():
    """获取向量库状态信息"""
    return get_collection_info()


@router.post("/vector-store/reset")
def reset_vector_store():
    """重置向量库（修复损坏）"""
    try:
        reset_collection()
        return {"status": "reset", "message": "向量库已重置"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/qa")
async def qa_endpoint(req: QARequest):
    cfg = get_complete_config()
    provider = req.provider if req.provider else cfg.get("provider", "openai")

    # Propagate LLM selection to all downstream calls
    from app.core.llm_context import set_llm_context
    set_llm_context(provider=provider)

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
        conv_history = _format_conversation_history_for_skill(req.messages)
        use_skill, skill_name, skill_params = skill_manager.should_use_skill(
            req.question, provider=provider, conversation_history=conv_history
        )
    
    # 让 stream_answer 完全处理检索逻辑，包括图搜索
    generation_params = {
        "top_k": req.top_k,
        "temperature": req.temperature,
        "top_p": req.top_p,
        "max_tokens": req.max_tokens,
        "presence_penalty": req.presence_penalty,
        "frequency_penalty": req.frequency_penalty,
        "enable_thinking": req.enable_thinking,
        "reasoning_effort": req.reasoning_effort,
        "use_react": req.use_react,
        "use_graph": req.use_graph,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "use_skill": use_skill,
        "skill_name": skill_name,
        "skill_params": skill_params,
    }
    
    # 总是使用流式响应，兼容前端期望的格式
    def event_generator():
        # 然后发送answer的stream，包含state事件
        for item in stream_answer(req.question, provider=provider, include_state=True, **generation_params):
            if isinstance(item, dict):
                # 处理所有 ReAct 相关事件
                item_type = item.get('type')
                if item_type in ['state', 'skill_result', 'reasoning_chunk',
                               'react_thought', 'react_thought_chunk', 'react_reasoning_chunk',
                               'react_action', 'react_observation', 'react_final_answer',
                               'react_steps', 'react_error', 'graph_sources']:
                    yield f"data: {json.dumps(item)}\n\n"
            else:
                # 这是一个content事件
                yield f"data: {json.dumps({'type': 'content', 'content': item})}\n\n"
        # 发送结束信号
        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# 嵌入模型管理相关API
class EmbeddingModeRequest(BaseModel):
    mode: str  # "local" 或 "openai"
    reset_collection: Optional[bool] = False


class EmbeddingModelRequest(BaseModel):
    model_name: str
    cache_dir: Optional[str] = None


@router.get("/embedding/models/recommended")
def get_recommended_embedding_models():
    """获取推荐的本地嵌入模型列表"""
    try:
        models = get_recommended_models()
        return {"status": "ok", "models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐模型列表失败: {str(e)}")


@router.get("/embedding/status")
def get_embedding_status():
    """获取当前嵌入服务状态"""
    try:
        cfg = load_config()
        mode = cfg.get("embedding_mode", "local")
        
        status = {
            "mode": mode,
            "config": {
                "local_embedding_model": cfg.get("local_embedding_model"),
                "openai_embedding_model": cfg.get("openai_embedding_model")
            }
        }
        
        # 尝试获取嵌入服务的实际状态
        try:
            current_mode = EmbeddingService.get_current_mode()
            status["initialized"] = True
            status["current_mode"] = current_mode
            if current_mode == "local":
                status["local_model"] = cfg.get("local_embedding_model")
        except Exception:
            status["initialized"] = False
            
        return {"status": "ok", "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取嵌入状态失败: {str(e)}")


@router.post("/embedding/mode")
def set_embedding_mode(req: EmbeddingModeRequest):
    """设置嵌入模式（local 或 openai）"""
    try:
        if req.mode not in ["local", "openai"]:
            raise HTTPException(status_code=400, detail="模式必须是 'local' 或 'openai'")
        
        # 更新配置
        cfg = load_config()
        cfg["embedding_mode"] = req.mode
        save_config(cfg)
        
        # 如果需要重置向量库
        if req.reset_collection:
            clear_all()
        
        return {
            "status": "ok", 
            "message": f"已切换到 {req.mode} 模式",
            "reset_collection": req.reset_collection
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换嵌入模式失败: {str(e)}")


@router.get("/document/preview")
def get_document_preview(filename: str, chunk_index: int = None):
    """
    获取文档预览内容
    
    Args:
        filename: 文档文件名
        chunk_index: 可选，指定chunk索引进行精确定位
    
    Returns:
        文档内容和元数据
    """
    from app.core.config import UPLOAD_DIR
    from app.services.ingest import extract_text
    
    try:
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
        
        # 提取文档全文
        full_text = extract_text(str(file_path))
        
        # 如果指定了chunk，尝试从向量库获取该chunk
        chunk_content = None
        if chunk_index is not None:
            try:
                from app.services.vector_store import init_collection
                collection = init_collection()
                # 获取该文档的所有chunks
                all_docs = collection.get(include=["documents", "metadatas"])
                if all_docs and all_docs.get("metadatas") and all_docs.get("documents"):
                    for i, metadata in enumerate(all_docs['metadatas']):
                        if (metadata.get('source') == filename and 
                            metadata.get('chunk_index') == chunk_index):
                            chunk_content = all_docs['documents'][i]
                            break
            except Exception as e:
                logger.debug("获取chunk失败: %s", e)
        
        return {
            "status": "ok",
            "filename": filename,
            "full_text": full_text,
            "chunk_content": chunk_content,
            "chunk_index": chunk_index
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档预览失败: {str(e)}")
    except Exception as e:
        logger.error("Document preview failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档预览失败: {str(e)}")


@router.post("/embedding/local-model")
def set_local_embedding_model(req: EmbeddingModelRequest):
    """设置本地嵌入模型"""
    try:
        cfg = load_config()
        cfg["local_embedding_model"] = req.model_name
        if req.cache_dir:
            cfg["local_model_cache_dir"] = req.cache_dir
        save_config(cfg)
        
        return {
            "status": "ok", 
            "message": f"本地模型已设置为: {req.model_name}",
            "model_name": req.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置本地模型失败: {str(e)}")


# 文档摘要管理 API
@router.get("/summaries")
def list_summaries():
    """列出所有文档摘要"""
    try:
        from app.services.summary_store import get_summary_store
        store = get_summary_store()
        summaries = store.get_all_summaries()
        
        summary_list = []
        for summary in summaries:
            summary_list.append({
                "filename": summary.filename,
                "summary": summary.summary,
                "key_topics": summary.key_topics,
                "quality_score": summary.quality_score,
                "generated_at": summary.generated_at
            })
        
        return {"status": "ok", "summaries": summary_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摘要列表失败: {str(e)}")


@router.get("/summaries/{filename:path}")
def get_summary(filename: str):
    """获取指定文档的摘要"""
    try:
        from app.services.summary_store import get_document_summary
        summary = get_document_summary(filename)
        
        if not summary:
            raise HTTPException(status_code=404, detail="摘要不存在")
        
        return {"status": "ok", "summary": summary.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摘要失败: {str(e)}")


@router.post("/summaries/{filename:path}/regenerate")
def regenerate_summary(filename: str, provider: str = None):
    """重新生成文档摘要"""
    try:
        from app.core.config import UPLOAD_DIR
        from app.services.ingest import extract_text, generate_and_save_summary
        from app.services.summary_store import get_document_summary
        
        cfg = load_config()
        if provider is None:
            provider = cfg.get("provider", "openai")
        
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 提取文本并重新生成摘要
        file_text = extract_text(str(file_path))
        success = generate_and_save_summary(str(file_path), filename, file_text, provider)
        
        if not success:
            raise HTTPException(status_code=500, detail="摘要生成失败")
        
        # 获取新生成的摘要
        summary = get_document_summary(filename)
        return {"status": "ok", "message": "摘要重新生成成功", "summary": summary.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成摘要失败: {str(e)}")
    except Exception as e:
        logger.error("Regenerate summary failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新生成摘要失败: {str(e)}")


# 上下文管理 API
@router.get("/context/{session_id}")
def get_context_history(session_id: str = "default"):
    """获取会话的上下文历史"""
    try:
        from app.services.context_manager import get_context_manager
        from app.core.config import load_config
        
        cfg = load_config()
        context_config = cfg.get("context_management", {})
        max_history = context_config.get("max_history_rounds", 5)
        
        context_mgr = get_context_manager(session_id, max_history=max_history)
        history = context_mgr.get_filtered_history(exclude_errors=False, exclude_questionable=False)
        stats = context_mgr.get_history_stats()
        
        return {"status": "ok", "history": history, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上下文历史失败: {str(e)}")


@router.delete("/context/{session_id}")
def clear_context_history(session_id: str = "default"):
    """清除会话的上下文历史"""
    try:
        from app.services.context_manager import clear_context_manager
        clear_context_manager(session_id)
        return {"status": "ok", "message": f"会话 {session_id} 的上下文历史已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除上下文历史失败: {str(e)}")


# === Merged from api/v1/routes.py ===

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int
    comment: Optional[str] = None


@router.get("/documents/{filename}")
def get_document_info(filename: str):
    """获取单个文档信息"""
    files = list_uploaded_files()
    for f in files:
        if f.get("filename") == filename:
            return f
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/{filename}/chunks")
def get_document_chunks(filename: str):
    """获取文档的所有chunks"""
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
    return {"filename": filename, "chunks": chunks, "total_chunks": len(chunks)}


@router.post("/qa/sync")
def qa_sync_endpoint(req: QARequest):
    """同步QA端点（非流式）"""
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
    """提交用户反馈"""
    logger.info("Received feedback for message %s: rating=%d, comment=%s", req.message_id, req.rating, req.comment)
    return {"success": True, "message_id": req.message_id}


# ── Graph visualization ──────────────────────────────────

@router.get("/graph/view")
def graph_view(force: bool = False):
    """浏览知识图谱 HTML，不存在时自动生成
    Args:
        force: 是否强制重新生成（用于新上传文档后）
    """
    path = "data/knowledge_graph.html"
    if force or not os.path.exists(path):
        from app.services.graph_analysis import GraphAnalyzer
        analyzer = GraphAnalyzer()
        analyzer.visualize(output_path=path)
    return FileResponse(path, media_type="text/html")


@router.get("/graph/visualize")
def graph_visualize(output: str = "data/knowledge_graph.html"):
    """生成知识图谱的交互式 HTML 可视化"""
    try:
        from app.services.graph_analysis import GraphAnalyzer
        analyzer = GraphAnalyzer()
        path = analyzer.visualize(output_path=output)
        return {"success": True, "path": path, "message": "可视化已生成"}
    except Exception as e:
        logger.error("Graph visualization failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
def graph_stats():
    """获取知识图谱统计信息"""
    try:
        from app.services.graph_store import get_graph_store
        store = get_graph_store()
        return {"success": True, "stats": store.stats()}
    except Exception as e:
        logger.error("Graph stats failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/communities")
def graph_communities():
    """获取图社区检测结果"""
    try:
        from app.services.graph_analysis import GraphAnalyzer
        analyzer = GraphAnalyzer()
        return {"success": True, "communities": analyzer.community_detection()}
    except Exception as e:
        logger.error("Graph communities failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
