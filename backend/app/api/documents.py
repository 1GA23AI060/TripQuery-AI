import shutil
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.database.models import Document, DocumentChunk
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentChunkResponse
)
from app.services.document_processor import document_processor, DocumentProcessingError
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload travel guide (PDF, TXT, DOCX), extract text, chunk, embed, and index into vector store.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Read bytes to check size
    contents = await file.read()
    file_size = len(contents)

    try:
        file_ext = document_processor.validate_file(file.filename, file_size)
    except DocumentProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Safe destination path
    dest_path = settings.UPLOAD_DIR / file.filename
    try:
        with open(dest_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed to write file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Could not save uploaded file")

    # Create document record in processing status
    doc = Document(
        filename=file.filename,
        file_type=file_ext,
        file_size=file_size,
        page_count=1,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # Extract text preserving pages
        pages_content, total_pages = document_processor.extract_content(dest_path, file_ext)
        doc.page_count = total_pages

        # Chunk document
        chunk_dicts = chunking_service.chunk_document(doc.id, pages_content)
        if not chunk_dicts:
            raise DocumentProcessingError("No extractable chunks found in document")

        # Save chunks to database
        db_chunks = []
        texts_to_embed = []
        for cd in chunk_dicts:
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=cd["chunk_index"],
                text=cd["text"],
                page_number=cd["page_number"]
            )
            db_chunks.append(chunk_rec)
            texts_to_embed.append(cd["text"])

        db.add_all(db_chunks)
        db.commit()

        # Refresh to get chunk IDs
        for ch in db_chunks:
            db.refresh(ch)

        # Generate embeddings
        embeddings = embedding_service.embed_texts(texts_to_embed)

        # Index into vector store
        chunk_ids = [ch.id for ch in db_chunks]
        doc_ids = [doc.id] * len(db_chunks)
        page_numbers = [ch.page_number for ch in db_chunks]

        vector_store.add_embeddings(
            chunk_ids=chunk_ids,
            document_ids=doc_ids,
            page_numbers=page_numbers,
            texts=texts_to_embed,
            embeddings=embeddings
        )

        doc.status = "ready"
        db.commit()
        db.refresh(doc)

        logger.info(f"Document {doc.filename} (ID: {doc.id}) processed successfully.")
        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            message="Document successfully processed and indexed"
        )

    except Exception as e:
        logger.error(f"Processing failed for {doc.filename}: {e}")
        doc.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process and index document: {str(e)}"
        )

@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    results = []
    for d in docs:
        c_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).count()
        results.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                file_size=d.file_size,
                page_count=d.page_count,
                status=d.status,
                uploaded_at=d.uploaded_at,
                chunk_count=c_count
            )
        )
    return results

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get single document with its chunks."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
    chunk_responses = [
        DocumentChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            text=c.text,
            page_number=c.page_number
        ) for c in chunks
    ]

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        page_count=doc.page_count,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
        chunk_count=len(chunks),
        chunks=chunk_responses
    )

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete document, associated database records, file, and remove vectors."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove vectors
    vector_store.delete_document(document_id)

    # Remove physical file if exists
    dest_path = settings.UPLOAD_DIR / doc.filename
    if dest_path.exists():
        try:
            dest_path.unlink()
        except Exception as e:
            logger.warning(f"Could not remove file {dest_path}: {e}")

    # Remove from database (cascades to chunks and sources)
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' deleted successfully", "id": document_id}
