import asyncio
import json

from asgiref.sync import sync_to_async
from torch.distributed.autograd import context

from .views import get_BNT_data, CLIENTS_IP

from channels.generic.websocket import AsyncWebsocketConsumer


class BNTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
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
        ip_address = self.scope['client'][0]
        if ip_address in CLIENTS_IP:
            CLIENTS_IP.remove(ip_address)
        await self.channel_layer.group_discard(
            'route_updates',
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def update_station(self, event):
        station_data = event['message']

        await self.send(text_data=json.dumps({
            'type': 'update_station',
            'message': station_data
        }))
