"""
Models for the Content Moderation Dashboard
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import secrets


class UserProfile(models.Model):
    """Extended user profile with API key management"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    api_calls_count = models.IntegerField(default=0)
    api_calls_limit = models.IntegerField(default=1000)  # Monthly limit
    is_api_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)
    
    def generate_api_key(self):
        """Generate a secure API key"""
        return f"cms_{secrets.token_urlsafe(32)}"
    
    def regenerate_api_key(self):
        """Regenerate API key"""
        self.api_key = self.generate_api_key()
        self.save()
        return self.api_key
    
    def increment_api_calls(self):
        """Increment API call counter"""
        self.api_calls_count += 1
        self.save()
    
    def can_make_api_call(self):
        """Check if user can make API calls"""
        return self.is_api_active and self.api_calls_count < self.api_calls_limit
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class ModerationRequest(models.Model):
    """Track moderation requests made through the dashboard"""
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_text = models.TextField(blank=True, null=True)
    content_image = models.ImageField(upload_to='moderation_images/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Results
    is_appropriate = models.BooleanField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    flagged_categories = models.JSONField(default=list, blank=True)
    moderation_result = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.content_type.title()} moderation by {self.user.username}"


class APIUsageLog(models.Model):
    """Log API usage for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.status_code}"


class SystemStats(models.Model):
    """Store system-wide statistics"""
    date = models.DateField(unique=True)
    total_requests = models.IntegerField(default=0)
    text_requests = models.IntegerField(default=0)
    image_requests = models.IntegerField(default=0)
    flagged_content = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "System Statistics"
    
    def __str__(self):
        return f"Stats for {self.date}"
