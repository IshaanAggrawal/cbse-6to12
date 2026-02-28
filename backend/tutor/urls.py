"""tutor/urls.py"""
from django.urls import path
from .views import AskView, DoubtHistoryView, HealthView

urlpatterns = [
    path('ask/',    AskView.as_view(),          name='ask'),
    path('doubts/', DoubtHistoryView.as_view(), name='doubt-history'),
    path('health/', HealthView.as_view(),       name='health'),
]
