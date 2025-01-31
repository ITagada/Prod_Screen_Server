import threading
import logging
import asyncio

from datetime import time

from django.http import HttpResponseRedirect
from django.shortcuts import render

from channels.layers import get_channel_layer
from mpmath import monitor
from scapy.all import sniff
from scapy.layers.inet import UDP
from scapy.packet import Raw

from .metro import *
from .moscow import SessionProtocolParser
from .consumers_moscow import MoscowConsumer


logging.basicConfig(level=logging.DEBUG)


LAST_PACKET_DATA = None

# Функция для запуска UDP-сервера
def packet_callback(packet):
    """
    Обрабатывает входящий сетевой пакет, преобразует его в HEX-строку
    и парсит с помощью SessionProtocolParser.
    """
    global LAST_PACKET_DATA
    try:
        if packet.haslayer(UDP):
            port = packet[UDP].sport
            if port == 29789:
                if Raw in packet:
                    if isinstance(packet[Raw].load, bytes):
                        raw_data = packet[Raw].load
                        LAST_PACKET_DATA = raw_data.hex()
                logging.info(f"Получен пакет с порта {port}, подключаем к MoscowConsumer")
                asyncio.run(send_redirect('/moscowBNT/'))
            elif port == 29788:
                logging.info(f"Получен пакет с порта {port}, подключаем к MoscowConsumer")
    except Exception as e:
        logging.error(f"Ошибка при обработке пакета: {e}")

async def send_redirect(url):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        'redirect_group',
        {
            'type': 'redirect_clients',
            'url': url,
        }
    )

def start_sniffing():
    sniff(prn=packet_callback, iface="enp6s0", filter='udp and port 29789', store=0, monitor=True)

def start_sniffing_thread():
    sniff_thread = threading.Thread(target=start_sniffing, daemon=True)
    sniff_thread.start()

def index(request):
    start_sniffing_thread()
    return render(request, 'Screen_Server/index.html')

def moscowBNT(request):
    global LAST_PACKET_DATA
    try:
        hex_data = LAST_PACKET_DATA if LAST_PACKET_DATA else ''
        parser = SessionProtocolParser(hex_data)
        parsed_data = parser.parse_packet() or {}
    except Exception as e:
        logging.error(f"Error parsing packet: {e}")
        parsed_data = {}
    return render(request, 'Screen_Server/moscowBNT.html', {'data': parsed_data})