"""
Document ingestion: extract text, split, add to vector store
"""
import os
from typing import List
from uuid import uuid4
from app.core.config import load_config
from app.services.vector_store import add_documents
import datetime


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


def ingest_file(path: str, provider: str = "openai") -> int:
    cfg = load_config()
    text = extract_text(path)
    chunks = split_text(text, cfg.get("chunk_size", 1000), cfg.get("chunk_overlap", 200))
    metas = []
    ids = []
    for i, c in enumerate(chunks):
        metas.append({
            "source": os.path.basename(path),
            "chunk_index": i,
            "ingest_time": datetime.datetime.utcnow().isoformat(),
        })
        ids.append(str(uuid4()))
    if chunks:
        add_documents(ids=ids, documents=chunks, metadatas=metas, provider=provider)
    return len(chunks)
