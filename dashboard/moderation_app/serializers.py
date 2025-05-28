"""
Serializers for the moderation app
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, ModerationRequest, APIUsageLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'api_key', 'api_calls_count', 'api_calls_limit', 
            'is_api_active', 'created_at', 'updated_at', 'usage_percentage'
        ]
        read_only_fields = ['api_key', 'api_calls_count', 'created_at', 'updated_at']
    
    def get_usage_percentage(self, obj):
        if obj.api_calls_limit > 0:
            return (obj.api_calls_count / obj.api_calls_limit) * 100
        return 0


class ModerationRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ModerationRequest
        fields = [
            'id', 'user', 'content_type', 'status', 'is_appropriate',
            'confidence_score', 'flagged_categories', 'moderation_result',
            'created_at', 'completed_at', 'processing_time_ms'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class APIUsageLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = APIUsageLog
        fields = [
            'id', 'user', 'endpoint', 'method', 'status_code',
            'response_time_ms', 'timestamp', 'ip_address'
        ]
        read_only_fields = ['id', 'user', 'timestamp']


class UserStatsSerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    text_requests = serializers.IntegerField()
    image_requests = serializers.IntegerField()
    flagged_content = serializers.IntegerField()
    avg_processing_time = serializers.FloatField()
    daily_stats = serializers.ListField()
    category_stats = serializers.DictField()
