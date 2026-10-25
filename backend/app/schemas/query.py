from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Destination or travel question")
    document_ids: Optional[List[int]] = Field(None, description="Optional filter by document IDs")

class SourceItem(BaseModel):
    document_id: int
    document_name: str
    page_number: int
    relevance_score: float
    retrieved_text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    question: Optional[str] = None
    created_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    vector_store: str
    documents_indexed: int
    chunks_indexed: int
