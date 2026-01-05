from django.utils.timezone import now
from .models import GlobalNotification

def global_notifications(request):
    notifications = GlobalNotification.objects.filter(
        is_active=True,
        show_on_site=True
    ).filter(
        expires_at__isnull=True
    ) | GlobalNotification.objects.filter(
        is_active=True,
        show_on_site=True,
        expires_at__gt=now()
    )

    return {
        'global_notifications': notifications
    }
