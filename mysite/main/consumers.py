# main/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

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
