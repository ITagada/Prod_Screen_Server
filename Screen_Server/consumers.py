import json

from .views import get_BNT_data

from channels.generic.websocket import AsyncWebsocketConsumer

class BNTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            'route_updates',
            self.channel_name
        )
        await self.accept()
        context = get_BNT_data()
        await self.send(text_data=json.dumps(context))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            'route_updates',
            self.channel_name
        )

    async def receive(self, text_data):
        message = json.loads(text_data)

        if message.get('action') == 'get_stops':
            await self.send(text_data=json.dumps(get_BNT_data()))

    async def update_station(self, event):
        station_data = event['message']

        await self.send(text_data=json.dumps({
            'type': 'update_station',
            'message': station_data
        }))
