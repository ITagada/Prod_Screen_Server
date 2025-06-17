import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RedirectConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer, который отвечает за пересылку сообщений редиректа всем подключённым клиентам.
    Используется для принудительной смены страницы на клиенте через WebSocket.
    """
    async def connect(self):
        """
        Обрабатывает подключение нового WebSocket-клиента.
        Добавляет клиента в группу "redirect_group" и принимает соединение.
        """
        self.room_group_name = "redirect_group"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """
        Обрабатывает отключение клиента от WebSocket.
        Удаляет клиента из группы "redirect_group".

        Аргументы:
            close_code (int): Код закрытия соединения.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def redirect_clients(self, event):
        """
        Получает событие с URL-адресом и отправляет его клиенту
        для выполнения перенаправления.

        Аргументы:
            event (dict): Словарь с ключом "url" — адрес для редиректа.
        """
        await self.send(text_data=json.dumps({
            "type": "redirect",
            "url": event["url"]
        }))
