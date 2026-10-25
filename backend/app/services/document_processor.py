import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pypdf
from docx import Document as DocxDocument
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessingError(Exception):
    pass

class DocumentProcessor:
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> str:
        """Validate file extension and file size."""
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise DocumentProcessingError(
                f"Unsupported file type '{ext}'. Allowed types: PDF, TXT, DOCX."
            )

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise DocumentProcessingError(
                f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB."
            )

        if file_size <= 0:
            raise DocumentProcessingError("Cannot process empty file.")

        return ext

    @classmethod
    def extract_content(cls, file_path: Path, file_type: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Extract text from file while strictly preserving page numbers.
        Returns:
            pages_content: List of dicts, each with 'page_number' and 'text'
            total_pages: Total count of pages
        """
        file_type = file_type.lower()
        if not file_path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")

        try:
            if file_type == ".pdf":
                return cls._extract_pdf(file_path)
            elif file_type == ".docx":
                return cls._extract_docx(file_path)
            elif file_type == ".txt":
                return cls._extract_txt(file_path)
            else:
                raise DocumentProcessingError(f"Unsupported format: {file_type}")
        except Exception as e:
            logger.error(f"Failed to extract content from {file_path}: {e}")
            raise DocumentProcessingError(f"Error parsing document: {str(e)}")

    @classmethod
    def _extract_pdf(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], int]:
        pages_content = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            if total_pages == 0:
                raise DocumentProcessingError("PDF document has 0 pages.")

            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = page_text.strip()
                if cleaned:
                    pages_content.append({
                        "page_number": page_idx + 1,
                        "text": cleaned
                    })

        if not pages_content:
            raise DocumentProcessingError("PDF does not contain any readable text.")

        return pages_content, total_pages

    @classmethod
    def _extract_docx(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], int]:
        doc = DocxDocument(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            raise DocumentProcessingError("DOCX document is empty.")

        # Estimate pages based on word count (~400 words per page standard)
        pages_content = []
        current_page_text = []
        current_word_count = 0
        current_page_num = 1

        for p in paragraphs:
            words = p.split()
            current_page_text.append(p)
            current_word_count += len(words)

            if current_word_count >= 400:
                pages_content.append({
                    "page_number": current_page_num,
                    "text": "\n\n".join(current_page_text)
                })
                current_page_text = []
                current_word_count = 0
                current_page_num += 1

        if current_page_text:
            pages_content.append({
                "page_number": current_page_num,
                "text": "\n\n".join(current_page_text)
            })

        total_pages = len(pages_content)
        return pages_content, total_pages

    @classmethod
    def _extract_txt(cls, file_path: Path) -> Tuple[List[Dict[str, Any]], int]:
        # Try UTF-8 first, fallback to latin-1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        if not content.strip():
            raise DocumentProcessingError("Text file is empty.")

        # Check for explicit form feed / page breaks (\x0c or \f)
        raw_pages = content.split("\x0c")
        if len(raw_pages) > 1:
            pages_content = []
            for i, p_text in enumerate(raw_pages):
                clean = p_text.strip()
                if clean:
                    pages_content.append({"page_number": i + 1, "text": clean})
            return pages_content, len(pages_content)

        # Otherwise divide by double line breaks into virtual pages (~450 words)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        pages_content = []
        current_page_text = []
        current_word_count = 0
        current_page_num = 1

        for p in paragraphs:
            words = p.split()
            current_page_text.append(p)
            current_word_count += len(words)

            if current_word_count >= 450:
                pages_content.append({
                    "page_number": current_page_num,
                    "text": "\n\n".join(current_page_text)
                })
                current_page_text = []
                current_word_count = 0
                current_page_num += 1

        if current_page_text:
            pages_content.append({
                "page_number": current_page_num,
                "text": "\n\n".join(current_page_text)
            })

        return pages_content, len(pages_content)

document_processor = DocumentProcessor()
