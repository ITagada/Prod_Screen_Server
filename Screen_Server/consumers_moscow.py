import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MoscowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'moscow_module_updates'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Если клиент что-то отправляет, но пока мы не обрабатываем это
        pass

    async def moscow_module_update(self, event):
        data = event['message']
        await self.send(text_data=json.dumps({
            'type': 'update',
            'message': data
        }))
