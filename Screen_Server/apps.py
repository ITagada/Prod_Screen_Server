import logging
import threading

from django.apps import AppConfig


class ScreenServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Screen_Server'

    def ready(self):
        from .views import start_sniffing_thread
        logging.info("🚀 Запускаем фоновый сниффер при старте сервера...")
        sniff_thread = threading.Thread(target=start_sniffing_thread, daemon=True)
        sniff_thread.start()
