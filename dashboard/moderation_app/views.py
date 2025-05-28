"""
Views for the Content Moderation Dashboard
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import requests
import json
import time
from .models import UserProfile, ModerationRequest, APIUsageLog, SystemStats
from .forms import CustomUserCreationForm, TextModerationForm, ImageModerationForm
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Home page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'moderation_app/home.html')


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile with API key
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Your API key has been generated.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Main dashboard"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's recent moderation requests
    recent_requests = ModerationRequest.objects.filter(user=request.user)[:10]
    
    # Get user statistics
    total_requests = ModerationRequest.objects.filter(user=request.user).count()
    text_requests = ModerationRequest.objects.filter(user=request.user, content_type='text').count()
    image_requests = ModerationRequest.objects.filter(user=request.user, content_type='image').count()
    flagged_content = ModerationRequest.objects.filter(user=request.user, is_appropriate=False).count()
    
    # API usage percentage
    usage_percentage = (profile.api_calls_count / profile.api_calls_limit) * 100 if profile.api_calls_limit > 0 else 0
    
    context = {
        'profile': profile,
        'recent_requests': recent_requests,
        'total_requests': total_requests,
        'text_requests': text_requests,
        'image_requests': image_requests,
        'flagged_content': flagged_content,
        'usage_percentage': usage_percentage,
    }
    return render(request, 'moderation_app/dashboard.html', context)


@login_required
def api_keys(request):
    """API key management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if 'regenerate' in request.POST:
            new_key = profile.regenerate_api_key()
            messages.success(request, 'API key regenerated successfully!')
        elif 'toggle_status' in request.POST:
            profile.is_api_active = not profile.is_api_active
            profile.save()
            status = 'activated' if profile.is_api_active else 'deactivated'
            messages.success(request, f'API key {status} successfully!')
    
    return render(request, 'moderation_app/api_keys.html', {'profile': profile})


@login_required
def test_moderation(request):
    """Test moderation interface"""
    text_form = TextModerationForm()
    image_form = ImageModerationForm()
    
    context = {
        'text_form': text_form,
        'image_form': image_form,
    }
    return render(request, 'moderation_app/test_moderation.html', context)


@login_required
def test_text_moderation(request):
    """Test text moderation"""
    if request.method == 'POST':
        form = TextModerationForm(request.POST)
        if form.is_valid():
            text_content = form.cleaned_data['text_content']
            user_id = form.cleaned_data.get('user_id', str(request.user.id))
            
            # Create moderation request record
            moderation_request = ModerationRequest.objects.create(
                user=request.user,
                content_type='text',
                content_text=text_content,
                status='pending'
            )
            
            try:
                start_time = time.time()
                
                # Call text moderation API
                response = requests.post(
                    'http://localhost:8000/moderate/text',
                    json={
                        'text': text_content,
                        'user_id': user_id,
                        'content_id': str(moderation_request.id)
                    },
                    timeout=30
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update moderation request
                    moderation_request.status = 'completed'
                    moderation_request.is_appropriate = result.get('is_appropriate', True)
                    moderation_request.confidence_score = result.get('confidence_score', 0.0)
                    moderation_request.flagged_categories = result.get('flagged_categories', [])
                    moderation_request.moderation_result = result
                    moderation_request.processing_time_ms = processing_time
                    moderation_request.completed_at = timezone.now()
                    moderation_request.save()
                    
                    # Increment user's API call count
                    profile, _ = UserProfile.objects.get_or_create(user=request.user)
                    profile.increment_api_calls()
                    
                    return JsonResponse({
                        'success': True,
                        'result': result,
                        'processing_time': processing_time,
                        'request_id': str(moderation_request.id)
                    })
                else:
                    moderation_request.status = 'failed'
                    moderation_request.save()
                    return JsonResponse({
                        'success': False,
                        'error': f'API returned status {response.status_code}: {response.text}'
                    })
                    
            except Exception as e:
                moderation_request.status = 'failed'
                moderation_request.save()
                logger.error(f"Text moderation error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error calling moderation API: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data'
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@login_required
def test_image_moderation(request):
    """Test image moderation"""
    if request.method == 'POST':
        form = ImageModerationForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data['image_file']
            user_id = form.cleaned_data.get('user_id', str(request.user.id))
            
            # Create moderation request record
            moderation_request = ModerationRequest.objects.create(
                user=request.user,
                content_type='image',
                content_image=image_file,
                status='pending'
            )
            
            try:
                start_time = time.time()
                
                # Prepare file for API call
                files = {'file': (image_file.name, image_file.file, image_file.content_type)}
                data = {
                    'user_id': user_id,
                    'content_id': str(moderation_request.id)
                }
                
                # Call image moderation API
                response = requests.post(
                    'http://localhost:8000/moderate/image',
                    files=files,
                    data=data,
                    timeout=30
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update moderation request
                    moderation_request.status = 'completed'
                    moderation_request.is_appropriate = result.get('is_appropriate', True)
                    moderation_request.confidence_score = result.get('confidence_score', 0.0)
                    moderation_request.flagged_categories = result.get('flagged_categories', [])
                    moderation_request.moderation_result = result
                    moderation_request.processing_time_ms = processing_time
                    moderation_request.completed_at = timezone.now()
                    moderation_request.save()
                    
                    # Increment user's API call count
                    profile, _ = UserProfile.objects.get_or_create(user=request.user)
                    profile.increment_api_calls()
                    
                    return JsonResponse({
                        'success': True,
                        'result': result,
                        'processing_time': processing_time,
                        'request_id': str(moderation_request.id)
                    })
                else:
                    moderation_request.status = 'failed'
                    moderation_request.save()
                    return JsonResponse({
                        'success': False,
                        'error': f'API returned status {response.status_code}: {response.text}'
                    })
                    
            except Exception as e:
                moderation_request.status = 'failed'
                moderation_request.save()
                logger.error(f"Image moderation error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error calling moderation API: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data'
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@login_required
def history(request):
    """Moderation history"""
    requests_list = ModerationRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'moderation_app/history.html', {'requests': requests_list})


@login_required
def analytics(request):
    """Analytics dashboard"""
    # User's personal analytics
    user_requests = ModerationRequest.objects.filter(user=request.user)
    
    # Time-based analytics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_requests = user_requests.filter(created_at__gte=thirty_days_ago)
    
    # Daily breakdown
    daily_stats = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        day_requests = user_requests.filter(created_at__date=date)
        daily_stats.append({
            'date': date.strftime('%m/%d'),
            'total': day_requests.count(),
            'text': day_requests.filter(content_type='text').count(),
            'image': day_requests.filter(content_type='image').count(),
            'flagged': day_requests.filter(is_appropriate=False).count(),
        })
    
    daily_stats.reverse()  # Show oldest to newest
    
    # Category breakdown
    flagged_requests = user_requests.filter(is_appropriate=False)
    category_stats = {}
    for request in flagged_requests:
        for category in request.flagged_categories:
            category_stats[category] = category_stats.get(category, 0) + 1
    
    # Performance metrics
    completed_requests = user_requests.filter(status='completed')
    avg_processing_time = completed_requests.aggregate(
        avg_time=Avg('processing_time_ms')
    )['avg_time'] or 0
    
    context = {
        'total_requests': user_requests.count(),
        'recent_requests': recent_requests.count(),
        'flagged_content': flagged_requests.count(),
        'daily_stats': daily_stats,
        'category_stats': category_stats,
        'avg_processing_time': round(avg_processing_time, 2),
    }
    
    return render(request, 'moderation_app/analytics.html', context)


@login_required
def documentation(request):
    """API documentation"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'moderation_app/documentation.html', {'profile': profile})
