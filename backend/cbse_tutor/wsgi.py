"""WSGI config for cbse_tutor project."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbse_tutor.settings')
application = get_wsgi_application()
