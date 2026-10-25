import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/query", tags=["query"])
logger = logging.getLogger(__name__)

@router.post("", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    """
    RAG Query endpoint:
    Processes user travel question, retrieves relevant chunks from FAISS vector store,
    generates grounded answer with source citations.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        response = rag_service.query(
            db=db,
            question=request.question,
            document_ids=request.document_ids
        )
        return response
    except Exception as e:
        logger.error(f"Error handling query: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
