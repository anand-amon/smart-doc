from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

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