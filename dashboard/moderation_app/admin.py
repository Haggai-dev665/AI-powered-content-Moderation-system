"""
Admin configuration for the moderation app
"""
from django.contrib import admin
from .models import UserProfile, ModerationRequest, APIUsageLog, SystemStats


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'api_calls_count', 'api_calls_limit', 'is_api_active', 'created_at']
    list_filter = ['is_api_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'api_key']
    readonly_fields = ['api_key', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'api_key')
        }),
        ('API Usage', {
            'fields': ('api_calls_count', 'api_calls_limit', 'is_api_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ModerationRequest)
class ModerationRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_type', 'status', 'is_appropriate', 'confidence_score', 'created_at']
    list_filter = ['content_type', 'status', 'is_appropriate', 'created_at']
    search_fields = ['user__username', 'content_text', 'flagged_categories']
    readonly_fields = ['id', 'created_at', 'completed_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('id', 'user', 'content_type', 'status')
        }),
        ('Content', {
            'fields': ('content_text', 'content_image')
        }),
        ('Results', {
            'fields': ('is_appropriate', 'confidence_score', 'flagged_categories', 'moderation_result')
        }),
        ('Metadata', {
            'fields': ('created_at', 'completed_at', 'processing_time_ms'),
            'classes': ('collapse',)
        }),
    )


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint', 'method', 'status_code', 'response_time_ms', 'timestamp']
    list_filter = ['method', 'status_code', 'timestamp']
    search_fields = ['user__username', 'endpoint', 'ip_address']
    readonly_fields = ['timestamp']
    
    date_hierarchy = 'timestamp'


@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_requests', 'text_requests', 'image_requests', 'flagged_content', 'average_response_time']
    list_filter = ['date']
    search_fields = ['date']
    
    date_hierarchy = 'date'
