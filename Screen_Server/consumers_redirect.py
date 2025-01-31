import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RedirectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "redirect_group"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def redirect_clients(self, event):
        await self.send(text_data=json.dumps({
            "type": "redirect",
            "url": event["url"]
        }))
