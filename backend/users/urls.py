"""users/urls.py"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, ChatSessionViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'sessions', ChatSessionViewSet, basename='session')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [path('', include(router.urls))]
