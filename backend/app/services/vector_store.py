import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int = 384, storage_dir: Optional[Path] = None):
        self.dimension = dimension
        self.storage_dir = storage_dir or settings.VECTOR_STORE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.storage_dir / "faiss_index.bin"
        self.metadata_file = self.storage_dir / "index_metadata.json"
        self.numpy_file = self.storage_dir / "vectors.npy"

        self.faiss_index = None
        self.numpy_embeddings: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []

        self._init_index()
        self.load()

    def _init_index(self):
        """Initialize empty index based on available backends."""
        if HAS_FAISS:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
        else:
            self.numpy_embeddings = np.empty((0, self.dimension), dtype=np.float32)
        self.metadata = []

    def add_embeddings(
        self,
        chunk_ids: List[int],
        document_ids: List[int],
        page_numbers: List[int],
        texts: List[str],
        embeddings: np.ndarray
    ) -> None:
        """
        Add batch of chunk embeddings and their metadata to the index.
        """
        if len(chunk_ids) == 0:
            return

        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        if HAS_FAISS and self.faiss_index is not None:
            self.faiss_index.add(embeddings)
        else:
            if self.numpy_embeddings is None or len(self.numpy_embeddings) == 0:
                self.numpy_embeddings = embeddings
            else:
                self.numpy_embeddings = np.vstack([self.numpy_embeddings, embeddings])

        # Store aligned metadata
        for c_id, doc_id, page_num, txt in zip(chunk_ids, document_ids, page_numbers, texts):
            self.metadata.append({
                "chunk_id": c_id,
                "document_id": doc_id,
                "page_number": page_num,
                "text": txt
            })

        self.save()

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
        threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        """
        Search for the top-k most relevant chunks meeting the threshold.
        """
        total_vectors = self.get_count()
        if total_vectors == 0:
            return []

        query_vec = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)
        candidate_k = min(total_vectors, max(top_k * 5, 20))

        if HAS_FAISS and self.faiss_index is not None:
            scores, indices = self.faiss_index.search(query_vec, candidate_k)
            scores = scores[0]
            indices = indices[0]
        else:
            # Normalized inner product equals cosine similarity
            sims = np.dot(self.numpy_embeddings, query_vec.T).flatten()
            indices = np.argsort(sims)[::-1][:candidate_k]
            scores = sims[indices]

        from app.services.embedding_service import embedding_service
        is_neural = embedding_service.is_neural
        minimum_score = threshold if is_neural else min(threshold, 0.3)

        results: List[Dict[str, Any]] = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.metadata):
                continue

            raw_score = float(score)
            calibrated_score = raw_score if is_neural else min(1.0, max(0.0, float(raw_score * 2.2)))

            if calibrated_score < minimum_score:
                continue

            meta = self.metadata[idx]
            if document_ids is not None and meta["document_id"] not in document_ids:
                continue

            item = dict(meta)
            item["relevance_score"] = round(calibrated_score, 4)
            results.append(item)

            if len(results) >= top_k:
                break

        return results

    def delete_document(self, document_id: int) -> None:
        """
        Remove all vectors and metadata associated with a given document_id.
        Rebuilds index with remaining vectors and persists.
        """
        remaining_indices = [
            i for i, meta in enumerate(self.metadata)
            if meta["document_id"] != document_id
        ]

        if len(remaining_indices) == len(self.metadata):
            return

        if HAS_FAISS and self.faiss_index is not None:
            remaining_embeddings = []
            for idx in remaining_indices:
                vec = self.faiss_index.reconstruct(idx)
                remaining_embeddings.append(vec)
            if remaining_embeddings:
                new_embeddings = np.vstack(remaining_embeddings).astype(np.float32)
            else:
                new_embeddings = np.empty((0, self.dimension), dtype=np.float32)
        else:
            new_embeddings = self.numpy_embeddings[remaining_indices] if remaining_indices else np.empty((0, self.dimension), dtype=np.float32)

        new_metadata = [self.metadata[i] for i in remaining_indices]

        self._init_index()
        if len(new_metadata) > 0:
            if HAS_FAISS and self.faiss_index is not None:
                self.faiss_index.add(np.ascontiguousarray(new_embeddings, dtype=np.float32))
            else:
                self.numpy_embeddings = new_embeddings
            self.metadata = new_metadata

        self.save()

    def get_count(self) -> int:
        """Return total count of indexed vectors."""
        if HAS_FAISS and self.faiss_index is not None:
            return self.faiss_index.ntotal
        return len(self.numpy_embeddings) if self.numpy_embeddings is not None else 0

    def save(self, directory: Optional[Path] = None) -> None:
        """Persist index and metadata to disk."""
        target_dir = directory or self.storage_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        index_path = target_dir / "faiss_index.bin"
        meta_path = target_dir / "index_metadata.json"
        numpy_path = target_dir / "vectors.npy"

        try:
            if HAS_FAISS and self.faiss_index is not None:
                faiss.write_index(self.faiss_index, str(index_path))
            elif self.numpy_embeddings is not None:
                np.save(str(numpy_path), self.numpy_embeddings)

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"Vector store saved ({self.get_count()} vectors).")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self, directory: Optional[Path] = None) -> None:
        """Load saved index and metadata from disk."""
        target_dir = directory or self.storage_dir
        index_path = target_dir / "faiss_index.bin"
        meta_path = target_dir / "index_metadata.json"
        numpy_path = target_dir / "vectors.npy"

        if not meta_path.exists():
            logger.info("No prior vector index found. Initialized clean store.")
            return

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                loaded_metadata = json.load(f)

            if HAS_FAISS and index_path.exists():
                self.faiss_index = faiss.read_index(str(index_path))
                self.metadata = loaded_metadata
                logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors.")
            elif numpy_path.exists():
                self.numpy_embeddings = np.load(str(numpy_path))
                self.metadata = loaded_metadata
                logger.info(f"Loaded NumPy vector index with {len(self.numpy_embeddings)} vectors.")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}. Reinitializing empty index.")
            self._init_index()

vector_store = VectorStore()
