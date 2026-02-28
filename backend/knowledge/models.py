"""knowledge/models.py — Tracks ingested NCERT documents."""

import uuid
from django.db import models


class IngestedDocument(models.Model):
    """Tracks which NCERT PDFs and syllabus files have been indexed into Pinecone."""

    class SourceType(models.TextChoices):
        PDF          = 'pdf',          'NCERT PDF'
        SYLLABUS_JSON = 'syllabus_json', 'Syllabus JSON'

    class StatusChoices(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        INDEXED  = 'indexed',  'Indexed'
        FAILED   = 'failed',   'Failed'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename     = models.CharField(max_length=255)
    source_type  = models.CharField(max_length=20, choices=SourceType.choices)
    subject      = models.CharField(max_length=30, blank=True, null=True)
    class_no     = models.IntegerField(null=True, blank=True)
    chunk_count  = models.IntegerField(default=0, help_text="Number of chunks indexed to Pinecone")
    status       = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    error_msg    = models.TextField(blank=True, null=True)
    indexed_at   = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['filename', 'source_type']

    def __str__(self):
        return f"{self.filename} [{self.status}]"
