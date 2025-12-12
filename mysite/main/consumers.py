import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract conversation user ID from URL
        self.conversation_user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope['user']
        
        # Create a unique room name for this conversation
        user_ids = sorted([self.user.id, int(self.conversation_user_id)])
        self.room_name = f"chat_{user_ids[0]}_{user_ids[1]}"
        self.room_group_name = f"chat_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket message from client"""
        data = json.loads(text_data)
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return
        
        # Save message to DB
        message_obj = await self.save_message(message_content)
        
        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name() or self.user.username,
                'timestamp': message_obj.sent_at.strftime('%I:%M %p'),
                'message_id': message_obj.id,
            }
        )
    
    async def chat_message(self, event):
        """Handle message event from group"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
        }))
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        other_user = User.objects.get(id=self.conversation_user_id)
        message = Message.objects.create(
            sender=self.user,
            receiver=other_user,
            content=content,
            is_read=False
        )
        return message
