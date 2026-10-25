import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database.database import init_db, SessionLocal
from app.database.models import Document, DocumentChunk
from app.services.document_processor import document_processor
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.rag_service import rag_service

def test_full_pipeline():
    print("Testing TripQuery AI Backend Pipeline...")
    init_db()
    vector_store.load()
    db = SessionLocal()

    demo_file = backend_dir / "data" / "demo" / "Bali_Travel_Guide.txt"
    assert demo_file.exists(), "Demo file does not exist"

    # Clean existing test docs
    db.query(Document).filter(Document.filename == "Bali_Travel_Guide.txt").delete()
    db.commit()

    # 1. Extract content
    pages, total_pages = document_processor.extract_content(demo_file, ".txt")
    print(f"Extracted {len(pages)} pages (Total: {total_pages})")
    assert len(pages) > 0

    # 2. Document record
    doc = Document(
        filename="Bali_Travel_Guide.txt",
        file_type=".txt",
        file_size=demo_file.stat().st_size,
        page_count=total_pages,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Chunk
    chunk_dicts = chunking_service.chunk_document(doc.id, pages)
    print(f"Created {len(chunk_dicts)} chunks")
    assert len(chunk_dicts) > 0

    db_chunks = []
    texts = []
    for cd in chunk_dicts:
        c = DocumentChunk(
            document_id=doc.id,
            chunk_index=cd["chunk_index"],
            text=cd["text"],
            page_number=cd["page_number"]
        )
        db_chunks.append(c)
        texts.append(cd["text"])

    db.add_all(db_chunks)
    db.commit()
    for c in db_chunks:
        db.refresh(c)

    # 4. Embeddings & Vector Store
    embeddings = embedding_service.embed_texts(texts)
    print(f"Generated embeddings array shape: {embeddings.shape}")
    assert embeddings.shape[0] == len(texts)

    vector_store.add_embeddings(
        chunk_ids=[c.id for c in db_chunks],
        document_ids=[doc.id] * len(db_chunks),
        page_numbers=[c.page_number for c in db_chunks],
        texts=texts,
        embeddings=embeddings
    )
    doc.status = "ready"
    db.commit()
    print("Indexed in vector store successfully!")

    # 5. Query
    question = "What are the best places to visit in Bali?"
    print(f"\nAsking Question: '{question}'")
    response = rag_service.query(db=db, question=question)

    print("\n" + "=" * 50)
    print("ANSWER:")
    print(response.answer)
    print("=" * 50)
    print(f"Retrieved {len(response.sources)} Sources:")
    for s in response.sources:
        print(f"- Doc: {s.document_name} | Page {s.page_number} | Relevance: {s.relevance_score * 100:.1f}%")
        print(f"  Excerpt: {s.retrieved_text[:120]}...\n")

    assert len(response.sources) > 0, "Expected at least 1 source retrieved"
    print("Pipeline test PASSED successfully!")
    db.close()

if __name__ == "__main__":
    test_full_pipeline()
