"""users/serializers.py — DRF serializers for Student, ChatSession, Message."""

from rest_framework import serializers
from .models import Student, ChatSession, Message


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Student
        fields = ['id', 'name', 'class_no', 'subject', 'language', 'created_at']
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['id', 'role', 'content', 'image', 'sources', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)
    messages      = MessageSerializer(many=True, read_only=True)

    class Meta:
        model  = ChatSession
        fields = ['id', 'student', 'class_no', 'subject', 'title', 'message_count', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'message_count']


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Slim serializer for creating a session (no nested messages)."""
    class Meta:
        model  = ChatSession
        fields = ['id', 'student', 'class_no', 'subject']
        read_only_fields = ['id']


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['id', 'session', 'role', 'content', 'image', 'sources']
        read_only_fields = ['id']
