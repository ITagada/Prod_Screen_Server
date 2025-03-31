import asyncio
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

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        stops = await sync_to_async(cache.get)("cached_STOPS")
        indices = await sync_to_async(cache.get)("cached_CURRENT_NEXT_INDEX") or {'current': 0, 'next': 1}
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

    async def query_switch(self, switch_ip):
        logging.info('Зашли в метод query_switch')
        try:
            await self.send(text_data=json.dumps({
                'action': 'get_connected_devices',
                'switchIp': switch_ip,
            }))

            response = await self.receive_response()
            return json.loads(response)
        except Exception as e:
            logging.error(f"Ошибка при запросе к коммутатору {switch_ip}: {e}")
            return {}

    async def receive_response(self):
        try:
            response = await asyncio.wait_for(self.receive(), timeout=5)
            response_data = json.loads(response)
            return response_data.get('text', '{}')
        except asyncio.TimeoutError:
            logging.warning("Тайм-аут при получении ответа от коммутатора")
            return '{}'
        except json.JSONDecodeError:
            logging.error("Ошибка при разборе JSON-ответа")
            return '{}'