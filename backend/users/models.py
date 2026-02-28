"""users/models.py — Student and Session models."""

import uuid
from django.db import models


class Student(models.Model):
    """Represents a CBSE student using the doubt solver."""

    class ClassChoices(models.IntegerChoices):
        CLASS_6  = 6,  'Class 6'
        CLASS_7  = 7,  'Class 7'
        CLASS_8  = 8,  'Class 8'
        CLASS_9  = 9,  'Class 9'
        CLASS_10 = 10, 'Class 10'
        CLASS_11 = 11, 'Class 11'
        CLASS_12 = 12, 'Class 12'

    class SubjectChoices(models.TextChoices):
        SCIENCE        = 'science',        'Science'
        SOCIAL_SCIENCE = 'social_science', 'Social Science'
        BOTH           = 'both',           'Both'

    class LanguageChoices(models.TextChoices):
        ENGLISH = 'english', 'English'
        HINDI   = 'hindi',   'Hindi'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=100, blank=True, null=True)
    class_no   = models.IntegerField(choices=ClassChoices.choices, null=True, blank=True)
    subject    = models.CharField(max_length=20, choices=SubjectChoices.choices, default=SubjectChoices.BOTH)
    language   = models.CharField(max_length=10, choices=LanguageChoices.choices, default=LanguageChoices.ENGLISH)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or 'Anonymous'} (Class {self.class_no})"


class ChatSession(models.Model):
    """A conversation session between a student and the AI tutor."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sessions')
    class_no   = models.IntegerField(null=True, blank=True)
    subject    = models.CharField(max_length=20, blank=True, null=True)
    title      = models.CharField(max_length=200, blank=True, null=True, help_text="Auto-generated from first question")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session {self.id} — {self.student}"

    @property
    def message_count(self):
        return self.messages.count()


class Message(models.Model):
    """A single message in a chat session."""

    class RoleChoices(models.TextChoices):
        USER      = 'user',      'User'
        ASSISTANT = 'assistant', 'Assistant'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session    = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=RoleChoices.choices)
    content    = models.TextField()
    image      = models.ImageField(upload_to='doubt_images/', null=True, blank=True)
    sources    = models.JSONField(default=list, help_text="Retrieved KB sources used for this answer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}..."
