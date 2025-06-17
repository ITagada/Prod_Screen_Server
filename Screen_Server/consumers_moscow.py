import asyncio
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async, async_to_sync
from .client_registry import ClientRegistry


registry = ClientRegistry()

class MoscowConsumer(AsyncWebsocketConsumer):
    """
    WebSocket-консьюмер для модуля Moscow.

    Обеспечивает:
    - регистрацию клиентов при подключении;
    - рассылку данных маршрута и состояния станций;
    - обработку обновлений через группу 'moscow_module_updates';
    - возможность опрашивать подключённые коммутаторы.

    Атрибуты:
        client_ip (str): IP клиента WebSocket-соединения.
        client_port (int): Порт клиента WebSocket-соединения.
        room_group_name (str): Название группы для рассылки обновлений.
    """
    async def connect(self):
        """
        Вызывается при установке WebSocket-соединения.

        - Регистрирует клиента в `ClientRegistry`.
        - Подключает к группе `moscow_module_updates`.
        - Отправляет клиенту текущее состояние маршрута (станции + индексы).
        """
        self.client_ip = self.scope['client'][0]
        self.client_port = self.scope['client'][1]
        self.room_group_name = 'moscow_module_updates'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await sync_to_async(registry.register)(self.client_ip, self.client_port, self.channel_name)
        stops = await sync_to_async(cache.get)("cached_STOPS")
        indices = await sync_to_async(cache.get)("cached_CURRENT_NEXT_INDEX") or {'current': 0, 'next': 1}
        await self.send(text_data=json.dumps({
            'start_stops': stops,
            'currentStationIndex': indices['current'],
            'nextStationIndex': indices['next'],
        }))

    async def disconnect(self, code):
        """
        Вызывается при отключении WebSocket-клиента.

        - Удаляет клиента из `ClientRegistry`.
        - Удаляет канал из группы рассылки.
        """
        await sync_to_async(registry.unregister)(self.client_ip, self.client_port)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Метод вызывается при получении сообщений от клиента.

        В текущей реализации — не обрабатывает входящие данные от клиента.
        """
        # Если клиент что-то отправляет, но пока мы не обрабатываем это
        pass

    async def moscow_module_update(self, event):
        """
        Отправляет обновление клиенту, вызванное событием `moscow_module_update`.

        Аргументы:
            event (dict): Словарь с ключом 'message', содержащим полезную нагрузку.
        """
        logging.info(f"Данные на сокете: {event}")
        await self.send(text_data=json.dumps({
            'type': 'update',
            'message': event['message']
        }))

    async def query_switch(self, switch_ip):
        """
        Выполняет запрос к клиенту-коммутатору по IP.

        Аргументы:
            switch_ip (str): IP-адрес коммутатора.

        Возвращает:
            dict: Ответ от клиента. Если ошибка — пустой словарь.
        """
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
        """
        Асинхронно ожидает ответа от клиента в течение 5 секунд.

        Возвращает:
            str: JSON-строка, содержащая поле `text`. Пустая строка при ошибке или тайм-ауте.
        """
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