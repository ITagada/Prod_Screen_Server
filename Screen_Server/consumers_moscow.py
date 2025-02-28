import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async


class MoscowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.client_ip = self.scope['client'][0]
        self.client_port = self.scope['client'][1]
        self.room_group_name = 'moscow_module_updates'

        client_params = await self.get_clients_params(self.client_ip, self.client_port)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        stops = await sync_to_async(cache.get)("cached_STOPS")
        indices = await sync_to_async(cache.get)("cached_CURRENT_NEXT_INDEX") or {'current': 0, 'next': 1}
        await self.send(text_data=json.dumps({'client_params': client_params}))
        await self.send(text_data=json.dumps({
            'start_stops': stops,
            'currentStationIndex': indices['current'],
            'nextStationIndex': indices['next'],
        }))

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

    @sync_to_async
    def get_clients_params(self, ip, port):

        key = f"{ip}:{port}"
        params = cache.get(key)
        if not params:
            params = {}
            cache.set(key, params, timeout=3600)
        return params
