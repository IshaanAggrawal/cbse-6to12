"""knowledge/serializers.py — DRF serializers for IngestedDocument."""

from rest_framework import serializers
from .models import IngestedDocument


class IngestedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = IngestedDocument
        fields = ['id', 'filename', 'source_type', 'subject', 'class_no', 'chunk_count', 'status', 'error_msg', 'indexed_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'indexed_at']
