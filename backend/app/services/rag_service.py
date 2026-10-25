import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service, INSUFFICIENT_EVIDENCE_MSG
from app.database.models import Document, DocumentChunk, Query, SourceReference
from app.schemas.query import QueryResponse, SourceItem

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.top_k = settings.TOP_K
        self.relevance_threshold = settings.RELEVANCE_THRESHOLD

    def query(
        self,
        db: Session,
        question: str,
        document_ids: Optional[List[int]] = None
    ) -> QueryResponse:
        """
        Execute full RAG pipeline:
        1. Embed question
        2. Vector search in FAISS/vector store
        3. Filter by relevance threshold and optional document_ids
        4. Look up document filenames from SQLite
        5. Pass retrieved context to LLM for grounded answer
        6. Persist Query and SourceReference records
        7. Return QueryResponse with answer and sources
        """
        clean_question = question.strip()
        if not clean_question:
            return QueryResponse(
                answer="Please enter a valid travel question.",
                sources=[],
                question=""
            )

        # 1. Embed question
        query_embedding = embedding_service.embed_query(clean_question)

        # 2. Vector search
        matched_chunks = vector_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            document_ids=document_ids,
            threshold=self.relevance_threshold
        )

        if not matched_chunks:
            # Save query with insufficient evidence answer
            db_query = Query(
                question=clean_question,
                answer=INSUFFICIENT_EVIDENCE_MSG
            )
            db.add(db_query)
            db.commit()

            return QueryResponse(
                answer=INSUFFICIENT_EVIDENCE_MSG,
                sources=[],
                question=clean_question,
                created_at=db_query.created_at
            )

        # 3. Enrich with document names from DB
        doc_ids = list({c["document_id"] for c in matched_chunks})
        docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {d.id: d.filename for d in docs}

        retrieved_contexts: List[Dict[str, Any]] = []
        source_items: List[SourceItem] = []

        for chunk in matched_chunks:
            d_id = chunk["document_id"]
            d_name = doc_map.get(d_id, "Travel Guide")
            item = {
                "document_id": d_id,
                "document_name": d_name,
                "page_number": chunk.get("page_number", 1),
                "relevance_score": float(chunk.get("relevance_score", 0.0)),
                "text": chunk.get("text", "")
            }
            retrieved_contexts.append(item)
            source_items.append(
                SourceItem(
                    document_id=d_id,
                    document_name=d_name,
                    page_number=chunk.get("page_number", 1),
                    relevance_score=float(chunk.get("relevance_score", 0.0)),
                    retrieved_text=chunk.get("text", "")
                )
            )

        # 4. Generate grounded answer
        answer = llm_service.generate_grounded_answer(clean_question, retrieved_contexts)

        # 5. Persist Query and Sources
        db_query = Query(
            question=clean_question,
            answer=answer
        )
        db.add(db_query)
        db.flush()

        for chunk in matched_chunks:
            ref = SourceReference(
                query_id=db_query.id,
                document_id=chunk["document_id"],
                chunk_id=chunk.get("chunk_id"),
                page_number=chunk.get("page_number", 1),
                relevance_score=float(chunk.get("relevance_score", 0.0)),
                retrieved_text=chunk.get("text", "")
            )
            db.add(ref)

        db.commit()
        db.refresh(db_query)

        return QueryResponse(
            answer=answer,
            sources=source_items,
            question=clean_question,
            created_at=db_query.created_at
        )

rag_service = RAGService()
