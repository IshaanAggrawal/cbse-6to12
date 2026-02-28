"""knowledge/urls.py"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IngestedDocumentViewSet, ReIndexView, KnowledgeStatsView

router = DefaultRouter()
router.register(r'docs', IngestedDocumentViewSet, basename='ingested-doc')

urlpatterns = [
    path('', include(router.urls)),
    path('reindex/', ReIndexView.as_view(),       name='reindex'),
    path('stats/',   KnowledgeStatsView.as_view(), name='kb-stats'),
]
