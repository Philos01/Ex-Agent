from pydantic import BaseModel
from typing import List, Optional


class DocumentMeta(BaseModel):
    filename: str
    upload_time: Optional[str]
    size: Optional[int]
    doc_type: Optional[str]


class QARequest(BaseModel):
    question: str
    top_k: int = 5
    provider: Optional[str] = None
    stream: bool = False
