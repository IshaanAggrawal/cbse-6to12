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
        f"You are an expert CBSE {class_str} {subj_str} tutor helping students solve doubts.\n\n"
        "STRICT RULES — follow without exception:\n"
        "1. Answer ONLY using the CONTEXT provided below. Do NOT use outside knowledge.\n"
        f"2. If the answer is not in the context, say exactly:\n"
        f'   "I don\'t have enough information about this in my CBSE {class_str} {subj_str} '
        f'knowledge base. Please refer to your NCERT textbook."\n'
        "3. NEVER make up facts, formulae, dates, or names.\n"
        "4. Use step-by-step explanations for concepts and numerical problems.\n"
        f"5. Keep language appropriate for CBSE {class_str} students.\n"
        f"6. {lang_note}\n"
        "7. At the end, mention the chapter/topic this came from (if in context)."
    )


def build_user_prompt(question: str, context_chunks: list[dict]) -> str:
    if not context_chunks:
        context_text = "No relevant content found in the CBSE knowledge base."
    else:
        parts = []
        for i, chunk in enumerate(context_chunks, 1):
            tag = chunk.get('chapter_title') or chunk.get('source', '')
            header = f"--- Context {i} [{tag}] ---" if tag else f"--- Context {i} ---"
            parts.append(f"{header}\n{chunk['text']}")
        context_text = "\n\n".join(parts)

    return (
        f"CONTEXT:\n{context_text}\n\n"
        f"STUDENT QUESTION:\n{question}\n\n"
        "Please solve/explain this doubt based ONLY on the context above."
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
