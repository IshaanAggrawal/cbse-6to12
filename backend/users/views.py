"""users/views.py — DRF viewsets for Student, ChatSession, Message."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Student, ChatSession, Message
from .serializers import (
    StudentSerializer,
    ChatSessionSerializer,
    ChatSessionCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    """
    /api/students/
    CRUD for student profiles.
    """
    queryset         = Student.objects.all()
    serializer_class = StudentSerializer

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """GET /api/students/{id}/sessions/ — list all sessions for a student."""
        student  = self.get_object()
        sessions = student.sessions.all()
        return Response(ChatSessionSerializer(sessions, many=True).data)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    /api/sessions/
    CRUD for chat sessions.
    """
    queryset = ChatSession.objects.select_related('student').prefetch_related('messages').all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ChatSessionCreateSerializer
        return ChatSessionSerializer

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """POST /api/sessions/{id}/add_message/ — append a message."""
        session = self.get_object()
        ser = MessageCreateSerializer(data={**request.data, 'session': session.id})
        if ser.is_valid():
            msg = ser.save()
            # Auto-title session from first user message
            if not session.title and request.data.get('role') == 'user':
                q = request.data.get('content', '')
                session.title = q[:80]
                session.save(update_fields=['title'])
            return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/messages/ — read-only (messages are created via /sessions/{id}/add_message/).
    """
    queryset         = Message.objects.all()
    serializer_class = MessageSerializer
