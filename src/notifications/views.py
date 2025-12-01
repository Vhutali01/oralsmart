from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q

from .models import Notification


@login_required
@require_http_methods(["GET"])
def notification_count(request):
    """
    API endpoint to get unread notification count
    """
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({
        'count': count,
        'has_unread': count > 0
    })


@login_required
@require_http_methods(["GET"])
def notification_list(request):
    """
    API endpoint to get recent notifications
    """
    limit = int(request.GET.get('limit', 10))
    
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related('referral', 'referral__patient')[:limit]
    
    data = [
        {
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'action_url': n.action_url,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'urgency_class': n.get_urgency_class(),
            'icon': n.get_icon(),
        }
        for n in notifications
    ]
    
    return JsonResponse({
        'notifications': data,
        'count': len(data)
    })


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """
    Mark a single notification as read
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'message': 'Notification marked as read'
    })


@login_required
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """
    Mark all notifications as read for current user
    """
    updated_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return JsonResponse({
        'success': True,
        'message': f'{updated_count} notification(s) marked as read',
        'count': updated_count
    })


@login_required
def notification_page(request):
    """
    Full page view of all notifications
    """
    # Filter options
    filter_type = request.GET.get('type', '')
    show_read = request.GET.get('show_read', 'false') == 'true'
    
    notifications = Notification.objects.filter(user=request.user)
    
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)
    
    if not show_read:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.select_related('referral', 'referral__patient')[:50]
    
    context = {
        'notifications': notifications,
        'filter_type': filter_type,
        'show_read': show_read,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'show_navbar': True,
    }
    
    return render(request, 'notifications/notification_list.html', context)
