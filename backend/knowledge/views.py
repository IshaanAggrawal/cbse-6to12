"""knowledge/views.py — Knowledge base management endpoints."""

import os
import subprocess
import sys
import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status

from .models import IngestedDocument
from .serializers import IngestedDocumentSerializer

logger = logging.getLogger(__name__)


class IngestedDocumentViewSet(ReadOnlyModelViewSet):
    """
    GET /api/knowledge/docs/ — list all indexed documents.
    GET /api/knowledge/docs/{id}/ — detail.
    """
    queryset         = IngestedDocument.objects.all()
    serializer_class = IngestedDocumentSerializer


class ReIndexView(APIView):
    """
    POST /api/knowledge/reindex/
    Triggers the ingester to re-index syllabus + new PDFs into Pinecone.
    Runs as a subprocess so it doesn't block the request.
    Only call this from an admin/internal context.
    """

    def post(self, request):
        ingester_path = os.path.join(settings.BASE_DIR, 'knowledge-base', 'ingester.py')

        if not os.path.exists(ingester_path):
            return Response({'error': 'Ingester script not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        python = sys.executable
        try:
            subprocess.Popen(
                [python, ingester_path],
                cwd=str(settings.BASE_DIR),
                env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'cbse_tutor.settings'},
            )
            return Response({'status': 'Indexing started in background. Check logs for progress.'})
        except Exception as e:
            logger.error(f"Failed to start ingester: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgeStatsView(APIView):
    """GET /api/knowledge/stats/ — Pinecone index stats."""

    def get(self, request):
        try:
            from pinecone import Pinecone
            pc    = Pinecone(api_key=settings.PINECONE_API_KEY)
            index = pc.Index(settings.PINECONE_INDEX)
            stats = index.describe_index_stats()
            return Response({
                'total_vectors':     stats.get('total_vector_count', 0),
                'index_name':        settings.PINECONE_INDEX,
                'embedding_model':   settings.EMBEDDING_MODEL,
                'documents_tracked': IngestedDocument.objects.count(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
