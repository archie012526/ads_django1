# main/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class PopularJobsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Name of the group
        self.group_name = "popular_jobs"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Called when jobs.update is broadcast
    async def jobs_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "jobs.update",
            "jobs": event["jobs"]
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        # Only allow authenticated users
        if self.user.is_authenticated:
            # Create user-specific group
            self.user_group_name = f"user_{self.user.id}_notifications"
            
            # Join user-specific group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Also join global notifications group
            await self.channel_layer.group_add(
                "global_notifications",
                self.channel_name
            )
            
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Leave user-specific group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
            # Leave global notifications group
            await self.channel_layer.group_discard(
                "global_notifications",
                self.channel_name
            )
    
    # Receive message from WebSocket (client)
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get("action") == "mark_read":
            notification_id = data.get("notification_id")
            await self.mark_notification_read(notification_id)
    
    # Handler for notification events
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": event["notification"]
        }))
    
    # Handler for global notification events
    async def global_notification_message(self, event):
        """Send global notification to WebSocket"""
        await self.send(text_data=json.dumps({
            "type": "global_notification",
            "notification": event["notification"]
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read in database"""
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
