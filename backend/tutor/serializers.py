"""tutor/serializers.py — DRF serializers for Doubt."""

from rest_framework import serializers
from .models import Doubt


class DoubtSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Doubt
        fields = ['id', 'session_id', 'question', 'answer', 'class_no', 'subject',
                  'language', 'has_image', 'sources', 'from_cache', 'model_used', 'created_at']
        read_only_fields = ['id', 'answer', 'sources', 'from_cache', 'model_used', 'created_at']


class AskSerializer(serializers.Serializer):
    """Validates incoming ask requests from the frontend."""
    question     = serializers.CharField(min_length=2, max_length=2000)
    class_no     = serializers.IntegerField(min_value=6, max_value=12, required=False, allow_null=True)
    subject      = serializers.ChoiceField(
        choices=['science', 'social_science'],
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    session_id   = serializers.UUIDField(required=False, allow_null=True)
    image_base64 = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    image_mime   = serializers.CharField(default='image/jpeg')
    stream       = serializers.BooleanField(default=True)
    language     = serializers.ChoiceField(choices=['english', 'hindi'], default='english')
