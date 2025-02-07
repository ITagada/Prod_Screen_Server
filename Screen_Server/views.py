import threading
import logging
import asyncio


from django.http import HttpResponseRedirect

from scapy.all import sniff
from scapy.layers.inet import UDP
from scapy.packet import Raw

from .metro import *
from .moscow import SessionProtocolParser


logging.basicConfig(level=logging.DEBUG)


LAST_PACKET_DATA = None
MODULE_STATE = None
MOSCOW_PORT = 29789
MOSCOW_CLIENT_RUNNING = False

# Функция для запуска UDP-сервера
def packet_callback(packet):
    """
    Обрабатывает входящий сетевой пакет, преобразует его в HEX-строку
    и парсит с помощью SessionProtocolParser.
    """
    global LAST_PACKET_DATA, MODULE_STATE
    try:
        if packet.haslayer(UDP):
            port = packet[UDP].sport
            if MODULE_STATE is None:
                if port == MOSCOW_PORT:
                    MODULE_STATE = 'moscow'
                    logging.info('Сервер переключен на модуль Moscow')
                    start_moscow_client()
                elif port != MOSCOW_PORT:
                    logging.info('Переключаем на другой модуль')

            elif MODULE_STATE == 'moscow':
                if Raw in packet and isinstance(packet[Raw].load, bytes):
                    LAST_PACKET_DATA = packet[Raw].load.hex()

    except Exception as e:
        logging.error(f'Ошибка при обработке пакета: {e}')


def start_sniffing():
    sniff(prn=packet_callback, iface="enp6s0", filter='udp and port 29789', store=0, monitor=True)

def start_sniffing_thread():
    sniff_thread = threading.Thread(target=start_sniffing, daemon=True)
    sniff_thread.start()

def index(request):
    global MODULE_STATE
    if MODULE_STATE is None:
        start_sniffing_thread()
    elif MODULE_STATE == 'moscow':
        return HttpResponseRedirect('/moscowBNT/')
    return render(request, 'Screen_Server/index.html')

def moscowBNT(request):
    return render(request, 'Screen_Server/moscowBNT.html')



def get_module_state(request):
    global MODULE_STATE
    return JsonResponse({'module_state': MODULE_STATE})


async def moscow_client():
    logging.info(f"Запуск UDP-клиента для порта {MOSCOW_PORT}")
    loop = asyncio.get_event_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: MoscowProtocol(),
        local_addr = ('0.0.0.0', MOSCOW_PORT),
    )

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        transport.close()


def start_moscow_client():
    global MOSCOW_CLIENT_RUNNING
    if MOSCOW_CLIENT_RUNNING:
        logging.warning("UDP-клиент уже запущен")
        return

    logging.info("🚀 Стартуем UDP-клиент...")
    MOSCOW_CLIENT_RUNNING = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(moscow_client())


class MoscowProtocol(asyncio.DatagramProtocol):
    """Кастомный протокол для обработки входящих и исходящих UDP-пакетов."""

    def connection_made(self, transport):
        self.transport = transport
        logging.info("UDP-соединение установлено")

    def datagram_received(self, data, addr):
        logging.info(f"Получены данные: {data.hex()}")
        hex_data = data.hex()
        parser = SessionProtocolParser(hex_data)
        parser.parse_packet()

    def send_diagnostics(selfself, message: bytes):
        logging.info(f"Отправлены диагностические данные: {message.hex()}")

    def error_received(self, error):
        logging.error(f"Ошибка UDP-соединения: {error}")

    def connection_lost(self, exc):
        logging.warning("UDP-соединение закрыто")