"""
URLs for the moderation app
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and authentication
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('test/', views.test_moderation, name='test_moderation'),
    path('history/', views.history, name='history'),
    path('analytics/', views.analytics, name='analytics'),
    path('docs/', views.documentation, name='documentation'),
    
    # AJAX endpoints for testing
    path('test/text/', views.test_text_moderation, name='test_text_moderation'),
    path('test/image/', views.test_image_moderation, name='test_image_moderation'),
]
