from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional, List, Dict

class ResultOut(BaseModel):
    id: str
    document_id: str
    ocr_confidence: float
    tokens_used: int
    api_cost: float
    extracted_json: dict
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy -> Pydantic

class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    stored_path: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProcessResponse(BaseModel):
    document: DocumentOut
    latest_result: ResultOut
    extracted_data: Optional[dict] = None

class AskRequest(BaseModel):
    query: str
    top_k: int = 6
    document_ids: Optional[List[str]] = None  # optional filter

class AskResponse(BaseModel):
    answer: str
    mode: str  # "rag" or "structured"
    sources: List[Dict[str, Any]]  # chunks + metadata