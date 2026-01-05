from .models import Notification, GlobalNotification

def employer_notifications(request):
    """Add notification data to all employer templates (and global site announcements)."""
    # Global site announcements (shown in admin base)
    global_notifications = GlobalNotification.objects.filter(show_on_site=True, is_active=True).order_by('-created_at')[:5]

    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'employer':
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return {
            'recent_notifications': recent_notifications,
            'unread_notifications_count': unread_notifications_count,
            'global_notifications': global_notifications,
        }
    return { 'global_notifications': global_notifications }
