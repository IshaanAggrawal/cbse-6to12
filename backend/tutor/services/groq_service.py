"""
tutor/services/groq_service.py
================================
Wraps Groq API calls:
  - Text completions (llama-3.1-8b-instant)
  - Vision completions for image questions (llama-4-scout)
  - Streaming generator for StreamingHttpResponse
  - Auto-fallback to gemma2-9b-it on rate limit
"""

import logging
from typing import Optional, Generator

from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)

# Sync Groq client (Django views are sync by default)
_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


# ── System prompt ─────────────────────────────────────────────────────────────
def build_system_prompt(class_no: Optional[int], subject: Optional[str], language: str) -> str:
    class_str = f"Class {class_no}" if class_no else "Classes 6–12"
    subj_str  = (subject or "Science and Social Science").replace("_", " ").title()
    lang_note = (
        "Respond in Hindi (Devanagari script). Keep scientific terms and formulae in English."
        if language == "hindi"
        else "Respond in clear, simple English suitable for school students."
    )
    return (
        f"You are an expert CBSE {class_str} {subj_str} tutor. You ONLY answer academic questions related to the CBSE Classes 6–12 syllabus.\n\n"
        "STRICT GUARDRAILS & RULES:\n"
        "1. SUBJECT LOCK: Strictly refuse to discuss anything unrelated to school education (e.g., politics, movies, celebrities, dating, games, or general non-academic gossip). For off-topic queries, say: \"I am a CBSE Tutor and can only assist you with academic doubts related to your syllabus.\"\n"
        "2. NO HALLUCINATION: If the information is not in the provided CONTEXT AND you don't have 100% factual academic knowledge about it, simply state that you don't know rather than guessing.\n"
        "3. DEPTH: Provide step-by-step explanations for mathematical and scientific concepts. Use simple language for Class 6 and professional language for Class 12.\n"
        "4. IMAGE ANALYSIS: If provided an image (e.g., a math problem or a diagram), analyze it carefully and solve it step-by-step.\n"
        f"5. LANGUAGE: {lang_note}\n"
        "6. CITATION: If using the provided context, mention the chapter/source at the end."
    )


def build_user_prompt(question: str, context_chunks: list[dict]) -> str:
    if not context_chunks:
        context_text = "No direct matches found in the specific textbook knowledge base for this query."
    else:
        parts = []
        for i, chunk in enumerate(context_chunks, 1):
            tag = chunk.get('chapter_title') or chunk.get('source', '')
            header = f"--- Context {i} [{tag}] ---" if tag else f"--- Context {i} ---"
            parts.append(f"{header}\n{chunk['text']}")
        context_text = "\n\n".join(parts)

    return (
        f"CONTEXT FROM TEXTBOOKS:\n{context_text}\n\n"
        f"STUDENT QUESTION:\n{question}\n\n"
        "Please provide a helpful and precise tutoring response."
    )


def build_vision_messages(system: str, user_text: str, image_b64: str, mime: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                {"type": "text", "text": user_text},
            ],
        },
    ]


# ── Streaming response ────────────────────────────────────────────────────────
def stream_response(
    question: str,
    context_chunks: list[dict],
    class_no: Optional[int] = None,
    subject: Optional[str] = None,
    language: str = "english",
    image_base64: Optional[str] = None,
    image_mime: str = "image/jpeg",
) -> Generator[str, None, None]:
    """
    Generator that yields text tokens as they arrive from Groq.
    Use with Django's StreamingHttpResponse.
    """
    is_vision = bool(image_base64)
    model     = settings.VISION_MODEL if is_vision else settings.PRIMARY_MODEL
    system    = build_system_prompt(class_no, subject, language)
    user_text = build_user_prompt(question, context_chunks)

    if is_vision:
        messages = build_vision_messages(system, user_text, image_base64, image_mime)
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_text},
        ]

    def _call(m: str):
        return get_client().chat.completions.create(
            model=m,
            messages=messages,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            stream=True,
        )

    try:
        stream = _call(model)
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token
    except Exception as e:
        logger.error(f"Groq error ({model}): {e}")
        # Fallback
        if model != settings.FALLBACK_MODEL:
            logger.info(f"Falling back to {settings.FALLBACK_MODEL}")
            try:
                for chunk in _call(settings.FALLBACK_MODEL):
                    token = chunk.choices[0].delta.content
                    if token:
                        yield token
            except Exception as e2:
                logger.error(f"Fallback error: {e2}")
                yield "\n[Error: AI service temporarily unavailable. Please try again.]"
        else:
            yield "\n[Error: AI service temporarily unavailable. Please try again.]"


# ── Non-streaming (for cached response) ──────────────────────────────────────
def get_response(
    question: str,
    context_chunks: list[dict],
    class_no: Optional[int] = None,
    subject: Optional[str] = None,
    language: str = "english",
    image_base64: Optional[str] = None,
    image_mime: str = "image/jpeg",
) -> tuple[str, str]:
    """Returns (answer_text, model_used)."""
    is_vision = bool(image_base64)
    model     = settings.VISION_MODEL if is_vision else settings.PRIMARY_MODEL
    system    = build_system_prompt(class_no, subject, language)
    user_text = build_user_prompt(question, context_chunks)

    if is_vision:
        messages = build_vision_messages(system, user_text, image_base64, image_mime)
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_text},
        ]

    def _call(m: str):
        return get_client().chat.completions.create(
            model=m,
            messages=messages,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            stream=False,
        )

    try:
        resp = _call(model)
        return resp.choices[0].message.content or "", model
    except Exception as e:
        logger.error(f"Groq error: {e}")
        if model != settings.FALLBACK_MODEL:
            try:
                resp = _call(settings.FALLBACK_MODEL)
                return resp.choices[0].message.content or "", settings.FALLBACK_MODEL
            except Exception:
                pass
        return "[Error: AI service unavailable]", model
