from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int

class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentChunkResponse(BaseModel):
    id: int
    chunk_index: int
    text: str
    page_number: int

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    page_count: int
    status: str
    uploaded_at: datetime
    chunk_count: Optional[int] = 0

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []
