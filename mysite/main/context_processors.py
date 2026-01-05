from django.db import models
from .models import Notification, GlobalNotification
from django.utils import timezone

def employer_notifications(request):
    """Add notification data to all authenticated users (employers, jobseekers, and global site announcements)."""
    # Global site announcements for ALL users (employers, jobseekers, admin)
    # Filter active notifications that haven't expired
    now = timezone.now()
    global_notifications = GlobalNotification.objects.filter(
        show_on_site=True, 
        is_active=True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    ).order_by('-created_at')[:5]

    if request.user.is_authenticated:
        # User-specific notifications for all authenticated users
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return {
            'recent_notifications': recent_notifications,
            'unread_notifications_count': unread_notifications_count,
            'global_notifications': global_notifications,
        }
    
    # For anonymous users, still provide global notifications
    return { 'global_notifications': global_notifications }
