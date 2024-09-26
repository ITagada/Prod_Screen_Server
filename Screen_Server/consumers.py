import json

from .views import get_BNT_data

from channels.generic.websocket import AsyncWebsocketConsumer

class BNTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        context = get_BNT_data()
        await self.send(text_data=json.dumps(context))

    async def disconnect(self, code):
        pass

    async def receive(self, text_data):
        message = json.loads(text_data)

        if message['action'] == 'get_stops':
            await self.send(text_data=json.dumps(get_BNT_data()))
