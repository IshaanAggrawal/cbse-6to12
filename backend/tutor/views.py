"""
tutor/views.py — DRF views for asking doubts.
Main endpoint: POST /api/ask/
"""

import hashlib
import logging

from django.core.cache import cache
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AskSerializer, DoubtSerializer
from .models import Doubt
from .services.rag_service import retrieve_context
from .services.groq_service import stream_response, get_response

logger = logging.getLogger(__name__)


def _answer_cache_key(question: str, class_no, subject: str) -> str:
    raw = f"answer:{question}:{class_no}:{subject}"
    return f"tutor:{hashlib.md5(raw.encode()).hexdigest()}"


class AskView(APIView):
    """
    POST /api/ask/
    Accepts text + optional image (base64), returns streamed or direct answer.
    """

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data        = serializer.validated_data
        question    = data['question']
        class_no    = data.get('class_no')
        subject     = data.get('subject')
        language    = data.get('language', 'english')
        image_b64   = data.get('image_base64')
        image_mime  = data.get('image_mime', 'image/jpeg')
        do_stream   = data.get('stream', True)
        session_id  = data.get('session_id')

        # ── Cache check (text-only questions) ─────────────────────────────────
        cache_key  = None
        from_cache = False
        if not image_b64:
            cache_key = _answer_cache_key(question, class_no, subject)
            cached = cache.get(cache_key)
            if cached:
                logger.info("Answer cache hit.")
                from_cache = True
                if do_stream:
                    def _cached_stream():
                        yield cached
                    return StreamingHttpResponse(_cached_stream(), content_type='text/plain')
                # Log it but don't re-save
                return Response({'answer': cached, 'from_cache': True, 'sources': []})

        # ── Retrieve relevant context from Pinecone ───────────────────────────
        context_chunks = retrieve_context(question, class_no, subject)

        # ── Streaming path ────────────────────────────────────────────────────
        if do_stream:
            def stream_and_save():
                tokens = []
                gen = stream_response(
                    question, context_chunks, class_no, subject,
                    language, image_b64, image_mime
                )
                for token in gen:
                    tokens.append(token)
                    yield token

                full_answer = "".join(tokens)

                # Cache and save to DB after streaming completes
                if cache_key and full_answer:
                    cache.set(cache_key, full_answer, timeout=3600)

                Doubt.objects.create(
                    question   = question,
                    answer     = full_answer,
                    class_no   = class_no,
                    subject    = subject,
                    language   = language,
                    has_image  = bool(image_b64),
                    sources    = context_chunks,
                    from_cache = False,
                    session_id = session_id,
                )

            return StreamingHttpResponse(stream_and_save(), content_type='text/plain')

        # ── Non-streaming path ─────────────────────────────────────────────────
        answer, model_used = get_response(
            question, context_chunks, class_no, subject, language, image_b64, image_mime
        )

        if cache_key:
            cache.set(cache_key, answer, timeout=3600)

        doubt = Doubt.objects.create(
            question   = question,
            answer     = answer,
            class_no   = class_no,
            subject    = subject,
            language   = language,
            has_image  = bool(image_b64),
            sources    = context_chunks,
            from_cache = False,
            model_used = model_used,
            session_id = session_id,
        )

        return Response({
            'id':         str(doubt.id),
            'answer':     answer,
            'from_cache': False,
            'model_used': model_used,
            'sources':    context_chunks,
        })


class DoubtHistoryView(APIView):
    """GET /api/doubts/?class_no=10&subject=science — Recent doubts."""

    def get(self, request):
        qs = Doubt.objects.all()
        class_no    = request.query_params.get('class_no')
        subject     = request.query_params.get('subject')
        session_id  = request.query_params.get('session_id')
        
        if session_id:
            qs = qs.filter(session_id=session_id)
        if class_no:
            qs = qs.filter(class_no=int(class_no))
        if subject:
            qs = qs.filter(subject=subject)
            
        qs = qs.order_by('created_at')[:50]
        return Response(DoubtSerializer(qs, many=True).data)


class HealthView(APIView):
    """GET /api/health/ — Quick health check."""
    def get(self, request):
        return Response({'status': 'ok', 'service': 'cbse-tutor-backend'})
