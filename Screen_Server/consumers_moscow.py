import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async


class MoscowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'moscow_module_updates'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        stops = await sync_to_async(cache.get)("cached_STOPS")
        await self.send(text_data=json.dumps({'start_stops': stops}))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Если клиент что-то отправляет, но пока мы не обрабатываем это
        pass

    async def moscow_module_update(self, event):
        logging.info(f"Данные на сокете: {event}")
        await self.send(text_data=json.dumps({
            'type': 'update',
            'message': event['message']
        }))
