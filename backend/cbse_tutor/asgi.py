"""ASGI config — plain HTTP only (no WebSocket routes)."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbse_tutor.settings')
application = get_asgi_application()
