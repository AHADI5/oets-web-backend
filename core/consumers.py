import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(
                f"user_{user.id}",
                self.channel_name
            )
            await self.accept()

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"user_{self.scope['user'].id}",
            self.channel_name
        )