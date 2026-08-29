# backend/app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class LoadStatusResponse(BaseModel):
    """数据载入状态响应"""
    status: str
    total_files: int
    total_documents: int
    file_details: List[dict]

class ChatRequest(BaseModel):
    """问答请求"""
    question: str
    top_k: Optional[int] = 5

class SourceDocument(BaseModel):
    """引用来源"""
    file_name: str
    content: str

class ChatResponse(BaseModel):
    """问答响应"""
    answer: str
    sources: List[SourceDocument]