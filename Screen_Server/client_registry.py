import threading
import logging

from typing import Dict, Tuple


class ClientRegistry:
    """
    Потокобезопасный реестр подключённых WebSocket-клиентов.
    Сопоставляет IP-адрес и порт клиента с именем его канала (channel_name).
    Используется для отслеживания подключений и маршрутизации сообщений.

    Формат ключей: (ip: str, port: int) → channel_name: str
    """
    def __init__(self):
        """
        Инициализирует пустой словарь клиентов и объект блокировки для обеспечения потокобезопасности.
        """
        self._clients: Dict[Tuple[str, int], str] = {}
        self._lock = threading.Lock()

    def register(self, ip: str, port: int, channel_name: str):
        """
        Регистрирует нового клиента по его IP, порту и имени канала.

        Аргументы:
            ip (str): IP-адрес клиента.
            port (int): Порт клиента.
            channel_name (str): Имя WebSocket-канала клиента.
        """
        with self._lock:
            self._clients[(ip, port)] = channel_name
            logging.info(f'Client registered {self._clients[(ip, port)]}')

    def unregister(self, ip: str, port: int):
        """
        Удаляет клиента из реестра по IP и порту.

        Аргументы:
            ip (str): IP-адрес клиента.
            port (int): Порт клиента.
        """
        with self._lock:
            self._clients.pop((ip, port), None)
            logging.info(f'Client unregistered {self._clients[(ip, port)]}')

    def get_channel_name(self, ip: str, port: int) -> str:
        """
        Возвращает имя канала клиента по IP и порту.

        Аргументы:
            ip (str): IP-адрес клиента.
            port (int): Порт клиента.

        Возвращает:
            str: channel_name клиента, если найден; иначе None.
        """
        with self._lock:
            logging.info(f'Get channel name {self._clients[(ip, port)]}')
            return self._clients.get((ip, port))

    def get_all_clients(self) -> Dict[Tuple[str, int], str]:
        """
        Возвращает копию текущего реестра клиентов.

        Возвращает:
            Dict[Tuple[str, int], str]: Словарь всех клиентов и их каналов.
        """
        with self._lock:
            logging.info(f'All clients {dict(self._clients)}')
            return dict(self._clients)

    def update(self, ip: str, port: int, channel_name: str):
        """
        Обновляет канал существующего клиента или регистрирует нового.

        Аргументы:
            ip (str): IP-адрес клиента.
            port (int): Порт клиента.
            channel_name (str): Новое имя канала клиента.
        """
        with self._lock:
            self._clients[(ip, port)] = channel_name
            logging.info(f'Update {self._clients[(ip, port)]}')
