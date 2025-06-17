"""
asgi.py

Точка входа для ASGI-приложения Django с поддержкой WebSocket через Django Channels.

Основные компоненты:
- HTTP-приложение через `get_asgi_application`
- WebSocket-приложение, обернутое в AuthMiddlewareStack для поддержки аутентификации
- URL-маршруты WebSocket подключаются через `routing.websocket_urlpatterns`
"""


import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from Screen_Server import routing

""" Тут происходит запуск сокета """

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'video.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})