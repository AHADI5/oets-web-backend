"""
API URL Configuration for core application

Defines all API endpoints including:
- JWT authentication endpoints
- Course resource endpoints
- Health checks
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CourseViewSet,
    health_check
)

# API Router Configuration
router = DefaultRouter()
router.register(
    r'courses',
    CourseViewSet,
    basename='course'
)

# JWT Authentication Patterns
auth_patterns = [
    path('obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]

# API v1 Patterns
v1_patterns = [
    path('auth/', include(auth_patterns)),
    path('health/', health_check, name='health_check'),
    path('', include(router.urls)),
]

urlpatterns = [
    path('v1/', include(v1_patterns)),
]