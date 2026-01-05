from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Notification, GlobalNotification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    """Broadcast new notifications to user via WebSocket"""
    if created:
        print(f"📨 Broadcasting notification {instance.id} to user {instance.user.id}")
        channel_layer = get_channel_layer()
        
        # Send notification to user-specific group
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user.id}_notifications",
            {
                "type": "notification_message",
                "notification": {
                    "id": instance.id,
                    "title": instance.title,
                    "message": instance.message,
                    "notification_type": instance.notification_type,
                    "is_read": instance.is_read,
                    "link": instance.link,
                    "created_at": instance.created_at.isoformat(),
                }
            }
        )
        print(f"✅ Notification {instance.id} broadcasted successfully")


@receiver(post_save, sender=GlobalNotification)
def broadcast_global_notification(sender, instance, created, **kwargs):
    """Broadcast new global notifications to all connected users"""
    if created and instance.is_active and instance.show_on_site:
        channel_layer = get_channel_layer()
        
        # Send notification to global group
        async_to_sync(channel_layer.group_send)(
            "global_notifications",
            {
                "type": "global_notification_message",
                "notification": {
                    "id": instance.id,
                    "title": instance.title,
                    "message": instance.message,
                    "level": instance.level,
                    "created_at": instance.created_at.isoformat(),
                }
            }
        )


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)