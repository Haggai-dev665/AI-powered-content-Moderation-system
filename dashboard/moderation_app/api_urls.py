"""
API URLs for the moderation app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'moderation-requests', api_views.ModerationRequestViewSet)
router.register(r'usage-logs', api_views.APIUsageLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('profile/', api_views.UserProfileAPIView.as_view(), name='api_profile'),
    path('stats/', api_views.UserStatsAPIView.as_view(), name='api_stats'),
    path('analytics/', api_views.AnalyticsAPIView.as_view(), name='api_analytics'),
    path('health/', api_views.SystemHealthAPIView.as_view(), name='api_health'),
]
