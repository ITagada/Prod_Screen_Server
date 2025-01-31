from django.urls import re_path

from . import consumers, consumers_moscow, consumers_redirect


""" Тут мы описываем маршрут открытия сокета"""
websocket_urlpatterns = [
    re_path(r'ws/bnt/$', consumers.BNTConsumer.as_asgi()),
    re_path(r'ws/moscow_module/$', consumers_moscow.MoscowConsumer.as_asgi()),
    re_path(r'ws/redirect/$', consumers_redirect.RedirectConsumer.as_asgi()),
]