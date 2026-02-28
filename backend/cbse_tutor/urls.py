"""cbse_tutor/urls.py — Root URL configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('tutor.urls')),
    path('api/', include('users.urls')),
    path('api/knowledge/', include('knowledge.urls')),

    # DRF browsable API auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve uploaded media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
