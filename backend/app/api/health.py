import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.database.models import Document, DocumentChunk
from app.services.vector_store import vector_store
from app.schemas.query import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("", response_model=HealthResponse)
def check_health(db: Session = Depends(get_db)):
    """
    Health check verifying database connectivity and vector store status.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    doc_count = db.query(Document).count()
    chunk_count = vector_store.get_count()

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="TripQuery AI",
        database=db_status,
        vector_store="ready",
        documents_indexed=doc_count,
        chunks_indexed=chunk_count
    )
