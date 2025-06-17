import logging
import threading

from django.apps import AppConfig


class ScreenServerConfig(AppConfig):
    """
    Конфигурация приложения Django для модуля `Screen_Server`.

    При запуске проекта автоматически запускается фоновый поток, который
    инициализирует сетевой сниффер (на базе Scapy) для прослушивания UDP-пакетов.
    Это позволяет серверу принимать данные от железнодорожных устройств в реальном времени.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Screen_Server'

    def ready(self):
        """
        Метод, вызываемый Django при запуске приложения.
        Здесь запускается фоновый поток с `start_sniffing_thread`, который начинает
        прослушивание UDP-портов. Поток отмечен как daemon, чтобы не мешать завершению работы сервера.
        """
        from .views import start_sniffing_thread
        logging.info("🚀 Запускаем фоновый сниффер при старте сервера...")
        sniff_thread = threading.Thread(target=start_sniffing_thread, daemon=True)
        sniff_thread.start()
