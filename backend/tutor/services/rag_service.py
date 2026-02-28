"""
tutor/services/rag_service.py
==============================
Core RAG pipeline:
  1. Embed question via sentence-transformers (local)
  2. Query Pinecone with class/subject filters
  3. Return relevant text chunks for grounding the LLM
"""

import hashlib
import logging
from typing import Optional
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ── Lazy singletons (loaded once at first use) ────────────────────────────────
_embedding_model = None
_pinecone_index  = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


def get_pinecone_index():
    global _pinecone_index
    if _pinecone_index is None:
        from pinecone import Pinecone
        api_key = settings.PINECONE_API_KEY
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY not configured in settings")
        pc = Pinecone(api_key=api_key)
        _pinecone_index = pc.Index(settings.PINECONE_INDEX)
        logger.info(f"Pinecone index '{settings.PINECONE_INDEX}' connected.")
    return _pinecone_index


# ── Cache key ─────────────────────────────────────────────────────────────────
def _cache_key(question: str, class_no: Optional[int], subject: Optional[str]) -> str:
    raw = f"retrieve:{question}:{class_no}:{subject}"
    return f"kb:{hashlib.md5(raw.encode()).hexdigest()}"


# ── Pinecone filter builder ───────────────────────────────────────────────────
def _build_filter(class_no: Optional[int], subject: Optional[str]) -> Optional[dict]:
    f = {}
    if class_no:
        f['class'] = {'$eq': class_no}
    if subject:
        f['subject'] = {'$eq': subject}
    return f or None


# ── Main retrieval function ───────────────────────────────────────────────────
def retrieve_context(
    question: str,
    class_no: Optional[int] = None,
    subject: Optional[str] = None,
    top_k: Optional[int] = None,
) -> list[dict]:
    """
    Retrieves the most relevant CBSE knowledge chunks from Pinecone.
    Returns list of dicts: {text, score, chapter_title, source, class_no, subject}
    """
    top_k = top_k or settings.TOP_K_RETRIEVAL
    cache_key = _cache_key(question, class_no, subject)

    # Check retrieval cache
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("Retrieval cache hit.")
        return cached

    model  = get_embedding_model()
    index  = get_pinecone_index()
    vector = model.encode(question, normalize_embeddings=True).tolist()

    try:
        results = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=_build_filter(class_no, subject),
        )
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        return []

    chunks = []
    for match in results.get('matches', []):
        score = match.get('score', 0)
        if score < 0.3:          # discard low-confidence
            continue
        meta = match.get('metadata', {})
        chunks.append({
            'text':          meta.get('text', ''),
            'score':         round(score, 4),
            'chapter_title': meta.get('chapter_title', ''),
            'source':        meta.get('source', ''),
            'class_no':      meta.get('class'),
            'subject':       meta.get('subject'),
        })

    cache.set(cache_key, chunks, timeout=1800)   # 30 min retrieval cache
    return chunks
