import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ChunkingService:
    def __init__(self, target_words: int = 500, overlap_words: int = 75):
        self.target_words = target_words
        self.overlap_words = overlap_words

    def chunk_document(
        self,
        document_id: int,
        pages_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk extracted document pages into 500-800 word segments with overlap,
        respecting sentence boundaries and retaining the original page numbers.
        """
        all_chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for page in pages_content:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "").strip()

            if not raw_text:
                continue

            page_chunks = self._chunk_page_text(raw_text, page_num, document_id, chunk_index)
            all_chunks.extend(page_chunks)
            chunk_index += len(page_chunks)

        logger.info(f"Generated {len(all_chunks)} chunks for document {document_id}")
        return all_chunks

    def _chunk_page_text(
        self,
        text: str,
        page_number: int,
        document_id: int,
        start_index: int
    ) -> List[Dict[str, Any]]:
        # Split text into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        # Break paragraphs down into sentences
        sentences = []
        for p in paragraphs:
            # Match sentences ending in punctuation
            parts = re.split(r'(?<=[.!?])\s+', p)
            for part in parts:
                cleaned = part.strip()
                if cleaned:
                    sentences.append(cleaned)

        if not sentences:
            sentences = [text]

        chunks = []
        current_chunk_sentences = []
        current_word_count = 0
        local_index = start_index

        for sent in sentences:
            words = sent.split()
            word_len = len(words)

            current_chunk_sentences.append(sent)
            current_word_count += word_len

            if current_word_count >= self.target_words:
                chunk_text = " ".join(current_chunk_sentences).strip()
                chunks.append({
                    "document_id": document_id,
                    "chunk_index": local_index,
                    "text": chunk_text,
                    "page_number": page_number
                })
                local_index += 1

                # Calculate overlap: keep trailing sentences that approximate overlap_words
                overlap_sentences = []
                overlap_count = 0
                for s in reversed(current_chunk_sentences):
                    s_words = len(s.split())
                    if overlap_count + s_words <= self.overlap_words or not overlap_sentences:
                        overlap_sentences.insert(0, s)
                        overlap_count += s_words
                    else:
                        break

                current_chunk_sentences = overlap_sentences
                current_word_count = overlap_count

        # Remainder chunk
        if current_chunk_sentences and current_word_count > 15:
            chunk_text = " ".join(current_chunk_sentences).strip()
            # If the remainder is tiny and we already made chunks, append to the last chunk
            if current_word_count < 40 and chunks:
                chunks[-1]["text"] += " " + chunk_text
            else:
                chunks.append({
                    "document_id": document_id,
                    "chunk_index": local_index,
                    "text": chunk_text,
                    "page_number": page_number
                })

        # Fallback if no chunk produced
        if not chunks:
            chunks.append({
                "document_id": document_id,
                "chunk_index": local_index,
                "text": text.strip(),
                "page_number": page_number
            })

        return chunks

chunking_service = ChunkingService()
