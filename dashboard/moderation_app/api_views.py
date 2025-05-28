"""
API Views for the moderation app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile, ModerationRequest, APIUsageLog
from .serializers import (
    UserProfileSerializer, ModerationRequestSerializer, 
    APIUsageLogSerializer, UserStatsSerializer
)


class UserProfileAPIView(APIView):
    """API view for user profile management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def post(self, request):
        """Regenerate API key"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if request.data.get('action') == 'regenerate_key':
            new_key = profile.regenerate_api_key()
            return Response({'api_key': new_key, 'message': 'API key regenerated successfully'})
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class ModerationRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for moderation requests"""
    queryset = ModerationRequest.objects.all()
    serializer_class = ModerationRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ModerationRequest.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent moderation requests"""
        recent_requests = self.get_queryset()[:10]
        serializer = self.get_serializer(recent_requests, many=True)
        return Response(serializer.data)


class APIUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for API usage logs"""
    queryset = APIUsageLog.objects.all()
    serializer_class = APIUsageLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return APIUsageLog.objects.filter(user=self.request.user)


class UserStatsAPIView(APIView):
    """API view for user statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get basic stats
        total_requests = ModerationRequest.objects.filter(user=user).count()
        text_requests = ModerationRequest.objects.filter(user=user, content_type='text').count()
        image_requests = ModerationRequest.objects.filter(user=user, content_type='image').count()
        flagged_content = ModerationRequest.objects.filter(user=user, is_appropriate=False).count()
        
        # Get processing time average
        avg_processing_time = ModerationRequest.objects.filter(
            user=user, status='completed'
        ).aggregate(avg_time=Avg('processing_time_ms'))['avg_time'] or 0
        
        # Get daily stats for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_stats = []
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            day_requests = ModerationRequest.objects.filter(user=user, created_at__date=date)
            daily_stats.append({
                'date': date.isoformat(),
                'total': day_requests.count(),
                'text': day_requests.filter(content_type='text').count(),
                'image': day_requests.filter(content_type='image').count(),
                'flagged': day_requests.filter(is_appropriate=False).count(),
            })
        
        daily_stats.reverse()
        
        # Category breakdown
        flagged_requests = ModerationRequest.objects.filter(user=user, is_appropriate=False)
        category_stats = {}
        for request in flagged_requests:
            for category in request.flagged_categories:
                category_stats[category] = category_stats.get(category, 0) + 1
        
        data = {
            'total_requests': total_requests,
            'text_requests': text_requests,
            'image_requests': image_requests,
            'flagged_content': flagged_content,
            'avg_processing_time': round(avg_processing_time, 2),
            'daily_stats': daily_stats,
            'category_stats': category_stats,
        }
        
        return Response(data)


class AnalyticsAPIView(APIView):
    """API view for analytics chart data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        chart_type = request.GET.get('chart', 'overview')
        
        if chart_type == 'overview':
            # Overview charts data
            total_requests = ModerationRequest.objects.filter(user=user).count()
            text_requests = ModerationRequest.objects.filter(user=user, content_type='text').count()
            image_requests = ModerationRequest.objects.filter(user=user, content_type='image').count()
            flagged_content = ModerationRequest.objects.filter(user=user, is_appropriate=False).count()
            
            return Response({
                'overview': {
                    'labels': ['Text Moderation', 'Image Moderation', 'Flagged Content'],
                    'data': [text_requests, image_requests, flagged_content],
                    'backgroundColor': ['#36A2EB', '#FF6384', '#FF9F40']
                }
            })
            
        elif chart_type == 'daily':
            # Daily activity chart
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_stats = []
            labels = []
            data = []
            
            for i in range(30):
                date = timezone.now().date() - timedelta(days=i)
                day_requests = ModerationRequest.objects.filter(user=user, created_at__date=date)
                labels.append(date.strftime('%m/%d'))
                data.append(day_requests.count())
            
            labels.reverse()
            data.reverse()
            
            return Response({
                'daily': {
                    'labels': labels,
                    'data': data,
                    'borderColor': '#36A2EB',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)'
                }
            })
            
        elif chart_type == 'categories':
            # Flagged categories breakdown
            flagged_requests = ModerationRequest.objects.filter(user=user, is_appropriate=False)
            category_stats = {}
            
            for request in flagged_requests:
                for category in request.flagged_categories:
                    category_stats[category] = category_stats.get(category, 0) + 1
            
            labels = list(category_stats.keys())
            data = list(category_stats.values())
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
            
            return Response({
                'categories': {
                    'labels': labels,
                    'data': data,
                    'backgroundColor': colors[:len(labels)]
                }
            })
            
        return Response({'error': 'Invalid chart type'}, status=400)


class SystemHealthAPIView(APIView):
    """API view for system health and insights"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Generate AI-powered insights
        total_requests = ModerationRequest.objects.filter(user=user).count()
        recent_requests = ModerationRequest.objects.filter(
            user=user, 
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        flagged_rate = 0
        if total_requests > 0:
            flagged_count = ModerationRequest.objects.filter(user=user, is_appropriate=False).count()
            flagged_rate = (flagged_count / total_requests) * 100
        
        # Generate insights based on data
        insights = []
        
        if recent_requests > 0:
            insights.append({
                'type': 'success',
                'title': 'Active Usage',
                'message': f'You have processed {recent_requests} requests in the last 7 days.',
                'action': 'Keep up the great work!'
            })
        
        if flagged_rate > 10:
            insights.append({
                'type': 'warning',
                'title': 'High Flag Rate',
                'message': f'{flagged_rate:.1f}% of your content is being flagged.',
                'action': 'Consider reviewing your content guidelines.'
            })
        elif flagged_rate < 5:
            insights.append({
                'type': 'info',
                'title': 'Low Flag Rate',
                'message': f'Only {flagged_rate:.1f}% of your content is flagged.',
                'action': 'Your content quality is excellent!'
            })
        
        if total_requests == 0:
            insights.append({
                'type': 'info',
                'title': 'Getting Started',
                'message': 'You haven\'t submitted any moderation requests yet.',
                'action': 'Try testing the moderation API to get started!'
            })
        
        return Response({
            'health_score': min(100, max(0, 100 - flagged_rate)),
            'insights': insights,
            'stats': {
                'total_requests': total_requests,
                'recent_requests': recent_requests,
                'flagged_rate': round(flagged_rate, 2)
            }
        })
