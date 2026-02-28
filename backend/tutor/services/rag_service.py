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
    """Disabled to save memory on Render Free tier."""
    return None


def get_pinecone_index():
    """Disabled to save memory on Render Free tier."""
    return None


# ── Cache key ─────────────────────────────────────────────────────────────────
def _cache_key(question: str, class_no: Optional[int], subject: Optional[str]) -> str:
    raw = f"retrieve:{question}:{class_no}:{subject}"
    return f"kb:{hashlib.md5(raw.encode()).hexdigest()}"


# ── Pinecone filter builder ───────────────────────────────────────────────────
def _build_filter(class_no: Optional[int], subject: Optional[str]) -> Optional[dict]:
    return None


# ── Main retrieval function ───────────────────────────────────────────────────
def retrieve_context(
    question: str,
    class_no: Optional[int] = None,
    subject: Optional[str] = None,
    top_k: Optional[int] = None,
) -> list[dict]:
    """
    BYPASSED: Memory-efficient mode (No RAG).
    Returns empty list to rely on LLM internal knowledge.
    """
    logger.info("RAG retrieval bypassed for memory efficiency.")
    return []
