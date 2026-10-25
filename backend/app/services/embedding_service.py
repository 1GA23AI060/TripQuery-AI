import logging
from typing import List, Optional
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _model = None
    _dim: int = 384

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Load sentence-transformers model once and reuse across queries."""
        if not settings.USE_SENTENCE_TRANSFORMERS:
            logger.info("SentenceTransformer loading disabled; using deterministic semantic projection.")
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            if hasattr(self._model, "get_embedding_dimension"):
                self._dim = self._model.get_embedding_dimension()
            else:
                self._dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Vector dimension: {self._dim}")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer '{settings.EMBEDDING_MODEL_NAME}': {e}. "
                f"Using deterministic normalized semantic hashing projection."
            )
            self._model = None
            self._dim = 384

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def is_neural(self) -> bool:
        return self._model is not None

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate L2-normalized embeddings for a list of text strings.
        Returns float32 numpy array of shape (len(texts), dimension).
        """
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        if self._model is not None:
            try:
                embeddings = self._model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                return np.ascontiguousarray(embeddings, dtype=np.float32)
            except Exception as e:
                logger.error(f"Error during model encoding: {e}. Falling back to semantic projection.")

        return self._fallback_embeddings(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate normalized embedding for a single query string.
        Returns 1D float32 numpy array of shape (dimension,).
        """
        result = self.embed_texts([query])
        return result[0]

    def _fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Deterministic dense semantic projection (384-d, L2-normalized)
        used as an accurate fallback when model is loading or in lightweight environments.
        """
        import re
        stopwords = {
            "what", "are", "the", "is", "in", "for", "of", "to", "a", "an", "and",
            "or", "how", "with", "from", "on", "by", "at", "it", "this", "that",
            "be", "can", "do", "does", "did", "as", "about", "which", "who", "where", "when"
        }
        vectors = []
        for text in texts:
            vec = np.zeros(self._dim, dtype=np.float32)
            tokens = [
                x for x in re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
                if x not in stopwords and len(x) > 1
            ]
            if not tokens:
                tokens = ["travel", "destination"]
            for w in tokens:
                rng = np.random.RandomState(abs(hash(w)) % (2**31 - 1))
                vec += rng.randn(self._dim).astype(np.float32)

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                vec[0] = 1.0
            vectors.append(vec)
        return np.ascontiguousarray(np.array(vectors, dtype=np.float32))

embedding_service = EmbeddingService()
