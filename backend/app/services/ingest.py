"""
Document ingestion: extract text, split, add to vector store
"""
import os
import logging
from typing import List
from uuid import uuid4
from app.core.config import load_config
from app.services.vector_store import add_documents
import datetime

logger = logging.getLogger(__name__)


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    text_parts = []
    try:
        if ext == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(path)
            for p in reader.pages:
                text_parts.append(p.extract_text() or "")
        elif ext == ".docx":
            from docx import Document

            doc = Document(path)
            for p in doc.paragraphs:
                text_parts.append(p.text)
        elif ext in (".txt", ".md"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text_parts.append(f.read())
        elif ext in (".pptx",):
            from pptx import Presentation

            prs = Presentation(path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_parts.append(shape.text)
        else:
            # fallback: try to read as text
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text_parts.append(f.read())
    except Exception:
        # return whatever we have
        pass
    return "\n".join(text_parts)


def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    if not text:
        return []
    chunks = []
    step = chunk_size - chunk_overlap
    if step <= 0:
        step = chunk_size
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk)
    return chunks


def generate_and_save_summary(
    file_path: str, 
    filename: str, 
    file_text: str, 
    provider: str = "openai"
) -> bool:
    """
    生成并保存文件摘要
    
    Args:
        file_path: 文件路径
        filename: 文件名
        file_text: 文件文本内容
        provider: LLM提供商
        
    Returns:
        是否成功
    """
    cfg = load_config()
    summary_config = cfg.get("summary_search", {})
    
    if not summary_config.get("auto_generate_summary", True):
        logger.info("自动生成摘要功能已关闭")
        return False
    
    try:
        from app.services.document_summary import generate_document_summary
        from app.services.summary_store import save_document_summary
        
        logger.info(f"开始生成文件摘要: {filename}")
        
        # 生成摘要
        summary = generate_document_summary(file_text, filename, provider)
        summary.file_path = file_path
        
        # 保存摘要
        success = save_document_summary(summary)
        
        if success:
            logger.info(f"文件摘要保存成功: {filename}, 质量评分: {summary.quality_score:.2f}")
        else:
            logger.error(f"文件摘要保存失败: {filename}")
        
        return success
        
    except Exception as e:
        logger.error(f"生成文件摘要时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def ingest_file(path: str, provider: str = "openai", generate_summary: bool = True) -> dict:
    """
    处理文件并添加到知识库
    
    Args:
        path: 文件路径
        provider: LLM提供商
        generate_summary: 是否生成摘要
        
    Returns:
        包含处理信息的字典
    """
    cfg = load_config()
    text = extract_text(path)
    filename = os.path.basename(path)
    
    result = {
        "filename": filename,
        "chunks_count": 0,
        "summary_generated": False,
        "success": False
    }
    
    # 生成并保存摘要
    if generate_summary:
        summary_success = generate_and_save_summary(path, filename, text, provider)
        result["summary_generated"] = summary_success
    
    chunks = split_text(text, cfg.get("chunk_size", 1000), cfg.get("chunk_overlap", 200))
    metas = []
    ids = []
    for i, c in enumerate(chunks):
        metas.append({
            "source": filename,
            "chunk_index": i,
            "ingest_time": datetime.datetime.utcnow().isoformat(),
        })
        ids.append(str(uuid4()))
    if chunks:
        add_documents(ids=ids, documents=chunks, metadatas=metas, provider=provider)
        result["chunks_count"] = len(chunks)
        result["success"] = True
        logger.info(f"文件 {filename} 处理完成，拆分为 {len(chunks)} 个文档片段")
    
    return result
