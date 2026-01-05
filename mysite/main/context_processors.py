from .models import Notification

def employer_notifications(request):
    """Add notification data to all employer templates"""
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'employer':
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return {
            'recent_notifications': recent_notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    return {}
