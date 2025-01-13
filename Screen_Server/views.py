import socket
from moscow import PacketFactory
from metro import *


def process_moscow_data(data: bytes):
    try:
        # Создаем пакет на основе данных
        packet = PacketFactory.create_packet(data)

        # Парсим данные из пакета
        parsed_data = packet.parse()

        # Логика обработки данных (например, печать или обработка)
        print(f"Обработанные данные: {parsed_data}")

        # Вы можете вернуть ответ клиенту, если нужно
        response = b"Данные обработаны успешно"
        return response
    except Exception as e:
        print(f"Ошибка при обработке данных Moscow: {e}")
        return b"Ошибка обработки данных"

def start_server():
    # Указываем порт для moscow.py
    MOSCOW_PORT = 29789
    # Указываем порт для metro.py (если будет нужен)
    METRO_PORT = 29788  # Для примера

    # Создаем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", MOSCOW_PORT))

    print(f"Сервер запущен и слушает порт {MOSCOW_PORT}")

    while True:
        # Принимаем данные
        data, address = server_socket.recvfrom(1024)
        print(f"Получены данные: {data} от {address}")

        # Логика обработки данных
        if server_socket.getsockname()[1] == MOSCOW_PORT:
            response = process_moscow_data(data)
        else:
            response = process_metro_data(data)

        # Отправляем ответ (если нужно)
        if response:
            server_socket.sendto(response, address)

if __name__ == "__main__":
    start_server()
