from datetime import time

from scapy.all import sniff
from scapy.layers.inet import UDP
import threading
import logging

from scapy.packet import Raw

from .metro import *
from .moscow import SessionProtocolParser


logging.basicConfig(level=logging.DEBUG)


# Функция для запуска UDP-сервера
def packet_callback(packet):
    """
    Обрабатывает входящий сетевой пакет, преобразует его в HEX-строку
    и парсит с помощью SessionProtocolParser.
    """
    try:
        if packet.haslayer(UDP) and packet[UDP].sport == 29789:
            if Raw in packet:
                if isinstance(packet[Raw].load, bytes):
                    raw_data = packet[Raw].load
                    hex_data = raw_data.hex()
                    logging.info(f"Получена HEX-строка: {hex_data}")

                    # Создаём объект SessionProtocolParser
                    parser = SessionProtocolParser(hex_data)
                    try:
                        # Вызываем метод парсинга пакета
                        parsed_packet = parser.parse_packet()

                        # Логируем результаты
                        logging.info(f"Результат парсинга: {parsed_packet}")
                    except ValueError as e:
                        logging.error(f"Ошибка при парсинге пакета: {e}")
                else:
                    logging.error("Полезная нагрузка не является байтовым объектом.")
            else:
                logging.info("Пакет не содержит слоя Raw (полезной нагрузки).")
    except Exception as e:
        logging.error(f"Ошибка при обработке пакета: {e}")


# Функция для запуска прослушивания
def start_sniffing():
    while True:
        try:
            logging.info("Запуск sniff...")
            sniff(prn=packet_callback, iface="enp6s0", filter="udp and port 29789", store=0)
        except Exception as e:
            logging.error(f"Ошибка в sniff: {e}")
            logging.info("Перезапуск sniff через 5 секунд...")
            time.sleep(5)

# Запуск прослушивания в отдельном потоке
def start_sniffing_thread():
    def sniffing_wrapper():
        while True:
            try:
                start_sniffing()
            except Exception as e:
                logging.error(f"Ошибка в потоке sniff: {e}")
                time.sleep(5)  # Перезапуск через 5 секунд

    sniff_thread = threading.Thread(target=sniffing_wrapper)
    sniff_thread.daemon = True
    sniff_thread.start()

# Ваша вьюха Django
from django.http import HttpResponse

def start_udp_server(request):
    # logging.info("Запуск прослушивания UDP пакетов на порту 29789...")
    start_sniffing_thread()
    return HttpResponse("Прослушивание UDP пакетов запущено в фоне.")
