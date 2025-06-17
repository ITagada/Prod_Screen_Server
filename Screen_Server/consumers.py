import asyncio
import json

from asgiref.sync import sync_to_async
from torch.distributed.autograd import context

from .views import get_BNT_data, CLIENTS_IP

from channels.generic.websocket import AsyncWebsocketConsumer


class BNTConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer, обрабатывающий подключение клиентских экранов БНТ.
    После подключения отправляет начальные данные и подписывается на обновления маршрута.
    """
    async def connect(self):
        """
        Обрабатывает подключение клиента:
        - Сохраняет IP в глобальном списке CLIENTS_IP (если ещё не сохранён),
        - Подключает клиента к группе 'route_updates',
        - Отправляет клиенту контекст маршрута (информация о линии, станциях и вагонах).
        """
        ip_address = self.scope['client'][0]
        if ip_address not in CLIENTS_IP:
            CLIENTS_IP.append(ip_address)

        await self.accept()

        await self.channel_layer.group_add(
            'route_updates',
            self.channel_name
        )

        context = await sync_to_async(get_BNT_data)(ip_address)
        await self.send(text_data=json.dumps({
            'type': 'connection_data',
            'data': context
        }))

    async def disconnect(self, code):
        """
        Обрабатывает отключение клиента:
        - Удаляет IP клиента из CLIENTS_IP,
        - Удаляет клиента из группы 'route_updates'.

        Аргументы:
            code (int): Код закрытия соединения.
        """
        ip_address = self.scope['client'][0]
        if ip_address in CLIENTS_IP:
            CLIENTS_IP.remove(ip_address)
        await self.channel_layer.group_discard(
            'route_updates',
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Обработчик входящих сообщений от клиента.
        Пока не реализован (pass).
        """
        pass

    async def update_station(self, event):
        """
        Обрабатывает событие обновления маршрута, отправленное в группу 'route_updates'.
        Пересылает клиенту обновлённые данные о текущей и следующей станции.

        Аргументы:
            event (dict): Должен содержать ключ 'message' с актуальной информацией о станции.
        """
        station_data = event['message']

        await self.send(text_data=json.dumps({
            'type': 'update_station',
            'message': station_data
        }))
