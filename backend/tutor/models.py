"""tutor/models.py — Doubt model (quick lookup/history)."""

import uuid
from django.db import models


class Doubt(models.Model):
    """
    Records every doubt asked, its answer, and the context it was grounded in.
    Useful for analytics, caching decisions, and audit.
    """

    class SubjectChoices(models.TextChoices):
        SCIENCE        = 'science',        'Science'
        SOCIAL_SCIENCE = 'social_science', 'Social Science'

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id    = models.UUIDField(null=True, blank=True, help_text="ChatSession UUID if linked")
    question      = models.TextField()
    answer        = models.TextField(blank=True, null=True)
    class_no      = models.IntegerField(null=True, blank=True)
    subject       = models.CharField(max_length=20, choices=SubjectChoices.choices, null=True, blank=True)
    language      = models.CharField(max_length=10, default='english')
    has_image     = models.BooleanField(default=False)
    sources       = models.JSONField(default=list, help_text="Pinecone chunks used for this answer")
    from_cache    = models.BooleanField(default=False)
    model_used    = models.CharField(max_length=80, blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['class_no', 'subject']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Doubt [{self.class_no}/{self.subject}]: {self.question[:80]}"
