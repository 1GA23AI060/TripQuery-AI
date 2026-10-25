import os
import re
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are TripQuery AI, a travel document assistant.

Answer the user's question using ONLY the retrieved context from the uploaded travel documents.

Do not invent information.

Do not fabricate locations, prices, dates, attractions, recommendations, or citations.

If the retrieved context does not contain enough information to answer the question, say:

"I couldn't find enough relevant information in your uploaded travel documents to answer this question reliably."

Keep answers clear, useful, and concise. Format with sections like 'Summary', 'Recommended Places', or 'Key Details' when appropriate."""

INSUFFICIENT_EVIDENCE_MSG = "I couldn't find enough relevant information in your uploaded travel documents to answer this question reliably."

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL or "gpt-4o-mini"
        self.base_url = settings.OPENAI_BASE_URL
        self._client = None

    def _get_client(self):
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = OpenAI(**kwargs)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        return self._client

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_contexts: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a strictly grounded answer to the travel question using ONLY the retrieved context.
        """
        if not retrieved_contexts:
            return INSUFFICIENT_EVIDENCE_MSG

        # Format context blocks clearly with source indicators
        context_blocks = []
        for i, ctx in enumerate(retrieved_contexts, 1):
            doc_name = ctx.get("document_name", "Travel Guide")
            page_num = ctx.get("page_number", 1)
            text = ctx.get("text", "").strip()
            context_blocks.append(
                f"[Source {i} | Document: {doc_name} | Page {page_num}]\n{text}"
            )

        combined_context = "\n\n---\n\n".join(context_blocks)

        user_content = f"""RETRIEVED TRAVEL DOCUMENT CONTEXT:
{combined_context}

USER QUESTION:
{question}

Provide a well-structured, clear, and grounded answer based strictly on the above context. If the context does not contain sufficient details to answer, reply exactly: "{INSUFFICIENT_EVIDENCE_MSG}"."""

        client = self._get_client()

        if client is not None:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.0,
                    max_tokens=700
                )
                answer = response.choices[0].message.content.strip()
                if not answer:
                    return INSUFFICIENT_EVIDENCE_MSG
                return answer
            except Exception as e:
                logger.error(f"OpenAI completion error: {e}. Falling back to extractive grounded synthesis.")

        # Fallback synthesis: extract most relevant sections from top context without hallucinating
        return self._extractive_grounded_fallback(question, retrieved_contexts)

    def _extractive_grounded_fallback(
        self,
        question: str,
        retrieved_contexts: List[Dict[str, Any]]
    ) -> str:
        """
        Deterministic, zero-hallucination fallback when no API key is provided.
        Synthesizes an answer using strictly exact excerpts from the top retrieved passages.
        """
        if not retrieved_contexts:
            return INSUFFICIENT_EVIDENCE_MSG

        stopwords = {
            "what", "are", "the", "is", "in", "for", "of", "to", "a", "an", "and",
            "or", "how", "with", "from", "on", "by", "at", "it", "this", "that",
            "can", "do", "does", "did", "as", "about", "which", "who", "where", "tell", "me"
        }
        q_words = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", question.lower())) - stopwords

        scored_blocks = []
        for ctx in retrieved_contexts[:5]:
            text = ctx.get("text", "")
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [
                    s.strip() for s in re.split(r'(?<=[.!?])\s+', text)
                    if len(s.strip()) > 20
                ]

            for block in paragraphs:
                b_lower = block.lower()
                b_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", b_lower))
                overlap = len(q_words & b_tokens)
                if overlap > 0:
                    scored_blocks.append((overlap, block))

        if not scored_blocks:
            top_text = retrieved_contexts[0].get("text", "")
            fallback_blocks = [p.strip() for p in top_text.split("\n\n") if len(p.strip()) > 30]
            if fallback_blocks:
                scored_blocks.append((1, fallback_blocks[0]))

        if not scored_blocks:
            return INSUFFICIENT_EVIDENCE_MSG

        scored_blocks.sort(key=lambda x: x[0], reverse=True)
        selected = []
        seen = set()
        for _, b in scored_blocks:
            if b not in seen:
                seen.add(b)
                selected.append(b)
            if len(selected) >= 3:
                break

        body = "\n\n".join(selected)

        # Structure clearly with headings if relevant
        places_section = ""
        q_lower = question.lower()
        if "place" in q_lower or "visit" in q_lower or "attraction" in q_lower:
            places_section = "\n\n### Recommended Places & Highlights\nRefer to the retrieved sections above for specific destination details, itineraries, and visitor tips."

        return (
            f"### Summary\n\n"
            f"{body}"
            f"{places_section}\n\n"
            f"> *Grounded in uploaded travel document context. Configure `OPENAI_API_KEY` in `backend/.env` for generative answers.*"
        )

llm_service = LLMService()
