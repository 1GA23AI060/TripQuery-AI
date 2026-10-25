from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, default=1)
    status = Column(String(50), default="processing")  # processing, ready, error
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    sources = relationship("SourceReference", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)

    document = relationship("Document", back_populates="chunks")
    sources = relationship("SourceReference", back_populates="chunk")

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sources = relationship("SourceReference", back_populates="query", cascade="all, delete-orphan")

class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True)
    page_number = Column(Integer, default=1)
    relevance_score = Column(Float, nullable=False)
    retrieved_text = Column(Text, nullable=False)

    query = relationship("Query", back_populates="sources")
    document = relationship("Document", back_populates="sources")
    chunk = relationship("DocumentChunk", back_populates="sources")
