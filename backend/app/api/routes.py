from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
import os
import json
import subprocess
import datetime
import shutil

from app.core.config import load_config, save_config, ensure_data_dirs, UPLOAD_DIR, METADATA_PATH
from app.services.ingest import ingest_file
from app.utils.file_utils import save_upload, list_uploaded_files, delete_uploaded_file
from app.services.qa import answer_question, stream_answer
from app.services.vector_store import get_collection_info, reset_collection, clear_all
from app.services.embedding import get_recommended_models, EmbeddingService
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["api"])


class Message(BaseModel):
    role: str  # "user" 或 "assistant"
    content: str


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
    messages: List[Message] = []  # 对话历史


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    cfg = load_config()
    ensure_data_dirs()
    saved = []
    failed = []  # 记录失败的文件
    
    for f in files:
        file_ext = os.path.splitext(f.filename)[1].lower()
        temp_path = None
        
        try:
            # 检查文件类型
            if file_ext in [".pdf", ".docx", ".doc"]:
                # 对于 PDF 文件，如果转换功能未启用，则直接上传
                if file_ext == ".pdf" and not cfg.get("allow_pdf_conversion", False):
                    print(f"[DEBUG] PDF 转换功能未启用，直接上传 PDF 文件: {f.filename}")
                    dest = await save_upload(f)
                    ingest_file(dest, provider=cfg.get("provider", "openai"))
                    saved.append(os.path.basename(dest))
                    print(f"[DEBUG] PDF 文件 {f.filename} 直接上传成功")
                    continue
                
                # 1. 先保存文件到临时位置
                temp_path = await save_upload(f)
                print(f"[DEBUG] 处理文件: {temp_path}")
                
                # 2. 根据文件类型选择转换脚本
                if file_ext == ".pdf":
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pdf2markdown.py")
                else:
                    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docx2markdown.py")
                
                # 使用专门的临时输出目录
                temp_output_dir = os.path.join(os.path.dirname(temp_path), "convert_temp")
                os.makedirs(temp_output_dir, exist_ok=True)
                
                print(f"[DEBUG] 运行转换脚本: {script_path}")
                
                # 使用虚拟环境中的python解释器
                python_exe = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", ".venv", "Scripts", "python.exe")
                if not os.path.exists(python_exe):
                    python_exe = "python"
                
                # 运行转换脚本，这次捕获输出以便显示错误
                result = subprocess.run(
                    [python_exe, script_path, temp_path, temp_output_dir],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                print(f"[DEBUG] 转换完成，返回码: {result.returncode}")
                if result.stderr:
                    print(f"[DEBUG] 转换输出: {result.stderr}")
                
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
                    
                    # 5. 更新元数据
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
                    
                    # 6. 加入知识库
                    ingest_file(final_md_path, provider=cfg.get("provider", "openai"))
                    saved.append(final_md_name)
                    print(f"[DEBUG] 文件 {f.filename} 处理成功")
                    
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
                print(f"[DEBUG] 跳过图片文件: {f.filename}")
                failed.append({"filename": f.filename, "reason": "不支持图片文件"})
                continue
            
            # 处理其他文件类型
            else:
                dest = await save_upload(f)
                ingest_file(dest, provider=cfg.get("provider", "openai"))
                saved.append(os.path.basename(dest))
                print(f"[DEBUG] 文件 {f.filename} 处理成功")
        
        except Exception as e:
            print(f"[ERROR] 文件 {f.filename} 处理失败: {e}")
            import traceback
            traceback.print_exc()
            failed.append({
                "filename": f.filename,
                "reason": str(e)
            })
            # 清理临时文件
            try:
                if temp_path and os.path.exists(temp_path):
                    delete_uploaded_file(os.path.basename(temp_path))
                    os.remove(temp_path)
            except:
                pass
            # 继续处理下一个文件，不中断整个流程
            continue
    
    # 返回结果，包含成功和失败的信息
    return {
        "status": "ok",
        "files": saved,
        "failed": failed,
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
    
    print(f"[DEBUG] 删除文档: {target_filename}")
    delete_uploaded_file(target_filename)
    return {"status": "deleted", "file": target_filename}


@router.post("/clear")
def clear_knowledge():
    from app.services.vector_store import clear_all

    clear_all()
    return {"status": "cleared"}


@router.get("/config")
def get_config():
    return load_config()


@router.post("/config")
def post_config(data: dict):
    cfg = load_config()
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
    cfg = load_config()
    provider = req.provider if req.provider else cfg.get("provider", "openai")
    
    # 调试日志
    print(f"[DEBUG] Received QA request with params:")
    print(f"[DEBUG]   question: {req.question[:50]}...")
    print(f"[DEBUG]   top_k: {req.top_k}")
    print(f"[DEBUG]   temperature: {req.temperature}")
    print(f"[DEBUG]   top_p: {req.top_p}")
    print(f"[DEBUG]   max_tokens: {req.max_tokens}")
    print(f"[DEBUG]   presence_penalty: {req.presence_penalty}")
    print(f"[DEBUG]   frequency_penalty: {req.frequency_penalty}")
    print(f"[DEBUG]   messages history: {len(req.messages)} messages")
    
    from app.services.vector_store import search
    docs = search(req.question, top_k=req.top_k, provider=provider)
    sources = [d.get("metadata", {}) for d in docs]
    
    # 收集生成参数
    generation_params = {
        "top_k": req.top_k,
        "temperature": req.temperature,
        "top_p": req.top_p,
        "max_tokens": req.max_tokens,
        "presence_penalty": req.presence_penalty,
        "frequency_penalty": req.frequency_penalty,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages]
    }
    
    # 判断是否应该显示引用材料
    def should_show_sources(question, sources_list):
        # 如果没有搜索结果，不显示
        if not sources_list or len(sources_list) == 0:
            return False
        
        # 检查是否是自我认知类问题
        self_identity_keywords = ['你是谁', '你叫什么', '你的名字', '你是', '你能做什么', '你基于什么', '谁开发的', '开发者', '你来自']
        for keyword in self_identity_keywords:
            if keyword in question:
                return False
        
        # 检查是否是纯闲聊问题
        casual_keywords = ['天气', '笑话', '故事', '聊天', '你好', '嗨', '哈喽', '早上好', '下午好', '晚上好']
        is_casual = any(keyword in question for keyword in casual_keywords)
        
        # 如果是闲聊且没有相关搜索结果，不显示
        if is_casual:
            # 简单检查搜索结果是否相关（这里简化处理）
            return True
        
        return True
    
    # 总是使用流式响应，兼容前端期望的格式
    def event_generator():
        # 只在需要时发送sources
        if should_show_sources(req.question, sources):
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        else:
            # 发送空sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
        # 然后发送answer的stream，包含state事件
        for item in stream_answer(req.question, provider=provider, include_state=True, **generation_params):
            if isinstance(item, dict) and item.get('type') == 'state':
                # 这是一个state事件
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
                print(f"[DEBUG] 获取chunk失败: {e}")
        
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
        import traceback
        traceback.print_exc()
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
