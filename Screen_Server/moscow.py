import socket
import struct
import logging
import json
import asyncio

from channels.utils import await_many_dispatch
from django.core.cache import cache

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime as dt

from Screen_Server.consumers_moscow import MoscowConsumer


class ByteParserBase:
    DATA_SIZE = {
        "int": 2,  # 2 символа HEX = 1 байт
        "float": 8,  # 8 символов HEX = 4 байта
        "int16": 4,  # 4 символа HEX = 2 байта
        "int32": 8,  # 8 символов HEX = 4 байта
        "byte": 2  # 2 символа HEX = 1 байт
    }

    def __init__(self, hex_data: str, sender_ip: str=None):
        self.data = hex_data
        self.offset = 0
        self.sender_ip = sender_ip

    def parse_packet(self):
        """
        Вызывает метод parse() у дочернего класса.
        """
        if hasattr(self, "parse"):
            return self.parse()
        raise NotImplementedError(f"Метод parse_packet не реализован в классе {self.__class__.__name__}")

    def read(self, data_type: str) -> Any:
        """
        Читает данные указанного типа из HEX-строки.
        """
        size = self.DATA_SIZE.get(data_type)

        if data_type == "str":
            length = int(self.data[self.offset:self.offset + 4], 16)
            self.offset += 4
            string_hex = self.data[self.offset:self.offset + length * 2]
            self.offset += length * 2
            return bytes.fromhex(string_hex).decode("utf-8")
        elif not size:
            raise ValueError(f"Invalid data type: {data_type}")

        if self.offset + size > len(self.data):
            raise ValueError(f"Not enough data to read {data_type} at offset {self.offset}")

        # Извлекаем необходимую часть строки
        raw_value = self.data[self.offset:self.offset + size]
        self.offset += size

        if data_type == "byte":
            return int(raw_value, 16)  # Преобразуем в целое число (1 байт)

        if data_type == "int":
            return int(raw_value, 16)  # Преобразуем в целое число (1 байт)

        if data_type == "int16":
            return int(raw_value, 16)  # Преобразуем в целое число (2 байта)

        if data_type == "int32":
            return int(raw_value, 16)  # Преобразуем в целое число (4 байта)

        if data_type == "float":
            # Преобразуем из HEX в float через struct
            return struct.unpack(">f", bytes.fromhex(raw_value))[0]

        raise ValueError(f"Unsupported data type: {data_type}")


class SessionProtocolParser(ByteParserBase):
    def __init__(self, hex_data: str):
        super().__init__(hex_data)
        self.channel_layer = get_channel_layer()
        # logging.info(f"Получена строка данных: {hex_data}")

        self.validate_marker()

    async def send_to_socket_async(self, data: dict):
        try:
            if data['dataType'] == 'ConfigureData':
                return
            else:
                await self.channel_layer.group_send(
                    'moscow_module_updates',
                    {
                        'type': 'moscow_module_update',
                        'message': data,
                    }
                )
                logging.info("Данные отправлены в WebSocket-группу 'moscow_module_updates'")
        except Exception as e:
            logging.error(f"Ошибка при отправке данных в WebSocket: {e}")

    def send_to_socket(self, data: dict):
        asyncio.create_task(self.send_to_socket_async(data))

    def validate_marker(self):
        marker = self.data[:8]
        if marker.lower() != 'ffa00010':
            logging.error(f"Неверный маркер: {marker}")
            raise ValueError(f"Invalid marker: {marker}")
        # logging.info(f"Маркер корректен: {marker}")
        self.offset += 8
        # logging.info(f"Смещение после валидации маркера = {self.offset}")

    def parse_field(self, field_name: str, data_type: str, validation_func=None):
        value = self.read(data_type)
        # logging.info(f"{field_name}: {value}")
        # logging.info(f"Смещение после чтения {field_name} = {self.offset}")

        if validation_func:
            validation_func(value)

        return value

    def parse_ip(self):
        ip_bytes = [self.read("byte") for _ in range(4)]
        ip_address = ".".join(str(byte) for byte in ip_bytes)
        # logging.info(f"Расшифрованный IP адрес: {ip_address}")
        return ip_address

    def calculate_crc(self, hex_data: str) -> int:
        data_bytes = bytes.fromhex(hex_data)
        crc = 0xFFFF
        for byte in data_bytes:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
        return crc

    async def parse_packet(self):
        # logging.info('Начинаем парсинг пакета...')
        try:
            header = {
                'receiver_ip': self.parse_ip(),
                'sender_ip': self.parse_ip(),
                'packet_id': self.parse_field('ID пакета', 'int16', lambda x: self.validate_packet_id(x)),
                'major_version': self.parse_field("Мажорная версия протокола", "int"),
                'minor_version': self.parse_field("Минорная версия протокола", "int"),
                'size': self.parse_field("Размер передаваемых данных", "int16"),
                'cs': self.parse_field("Контрольная сумма", "int16"),
            }

            original_cs = header['cs']

            cs_offset = self.offset - 4
            zeroed_data = self.data[:cs_offset] + "0000" + self.data[cs_offset + 4:]

            recalculated_crc = self.calculate_crc(zeroed_data)

            # logging.info(f"Оригинальный CRC: {original_cs}")
            # logging.info(f"Пересчитанный CRC: {recalculated_crc}")

            if recalculated_crc != original_cs:
                logging.error("Контрольная сумма пакета не совпадает. Пакет будет пропущен")
                return {
                    'header': header,
                    'payload': None,
                    'status': 'error',
                    'error_message': 'Invalid CRC',
                }

            sender_ip = header['sender_ip']
            payload = self.data[self.offset:]
            # logging.info(f"Полезная нагрузка: {payload}")

            if header['size'] > 0:
                payload_parser = PacketFactory.create_packet(payload, sender_ip)
                if asyncio.iscoroutinefunction(payload_parser.parse_packet):
                    payload = await payload_parser.parse_packet()
                else:
                    payload = payload_parser.parse_packet()

            parsed_data = {
                'header': header,
                'payload': payload,
                'status': 'success',
            }

            self.send_to_socket(parsed_data['payload'])

            # logging.info(f"Распаршенный пакет: {parsed_data}")

            return parsed_data

        except Exception as e:
            logging.error(f"Ошибка при парсинге пакета: {e}")
            return {
                'header': None,
                'payload': None,
                'status': 'error',
                'error_message': str(e),
            }

    def validate_packet_id(self, packet_id):
        if packet_id == 0:
            logging.info('ID пакета = 0: подтверждение не требуется.')
        elif not (1 <= packet_id <= 65535):
            raise ValueError(f"Incorrect packet ID: {packet_id}")


def find_station_index(next_station_id: int) -> Tuple[Optional[int], Optional[int]]:
    next_index = None
    current_index = None

    stops = cache_get('STOPS')

    if not stops:
        logging.error('cached_STOPS отсутствует в кэше или равно None')
        return current_index, next_index

    for i, stop in enumerate(stops):
        if stop['stationID'] == next_station_id:
            next_index = i
            current_index = i - 1 if i > 0 else None
            break

    return current_index, next_index


class OperationalData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("time", "str"),
        ("latitude", "float"),
        ("longitude", "float"),
        ("speed", "int"),
        ("mode", "byte"),
        ("nextStationID", "int32"),
        ("nextStationDistance", "int32"),
        ("nextStationSide", "byte"),
        ("nextStationPathNum", "int"),
        ("doorState", "byte")
    ]

    def parse(self) -> Dict[str, Any]:
        parsed_data = {
            'dataType': self.__class__.__name__,
        }
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        next_station_id = parsed_data['nextStationID']
        current_index, next_index = find_station_index(next_station_id)

        parsed_data['currentStationIndex'] = current_index
        parsed_data['nextStationIndex'] = next_index

        logging.info(f"Кэшируем индексы: current={current_index}, next={next_index}")
        cache_set('CURRENT_NEXT_INDEX', {'current': current_index, 'next': next_index})

        logging.info(f"Отработал класс OperationalData")
        return parsed_data

class AdditionalOperationalData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("outsideTemp", "int"),
        ("count", "int"),
    ]

    def parse(self) -> Dict[str, Any]:
        parsed_data = {
            'dataType': self.__class__.__name__,
        }
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        count = parsed_data["count"]
        for i in range(1, count + 1):
            parsed_data[f'id{i}'] = self.read("int")
            parsed_data[f'train{i}'] = self.read("int")
            parsed_data[f'temp{i}'] = self.read("int")
            parsed_data[f'passengers{i}'] = self.read("int")

        logging.info(f"Отработал класс AdditionalOperationalData")
        return parsed_data


def get_stops_position(route_data):
    stops = []
    line_length = 100
    start_position = 0
    stations = route_data['stations']
    total_stops = len(stations)

    if total_stops > 1:
        step = line_length / (total_stops - 1)
    else:
        step = 0

    for i, (key, station) in enumerate(stations.items(), start=1):
        station_name_key = f'stationName{i}'
        station_id_key = f'stationID{i}'
        arrive_timestamp_key = f'arriveTimestamp{i}'
        departure_timestamp_key = f'departureTimestamp{i}'

        stop_info = {
            'stationName': station.get(station_name_key, f"station{i}"),
            'stationID': station.get(station_id_key, i),
            'arriveTimestamp': station.get(arrive_timestamp_key, "00:00:00"),
            'departureTimestamp': station.get(departure_timestamp_key, "00:00:00"),
            'position': round(start_position, 3),
        }

        stops.append(stop_info)
        start_position += step

    return stops

# def add_position(func):
#     def wrapper(*args, **kwargs):
#         parsed_data = func(*args, **kwargs)
#         if 'stations' in parsed_data:
#             parsed_data['stops'] = get_stops_position(parsed_data)
#             del parsed_data['stations']
#         return parsed_data
#     return wrapper


class RouteData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("trainNumber", "str"),
        ("headSign", "str"),
        ("routeNumber", "int"),
        ("count", "int"),
    ]

    def __init__(self, hex_data: str, sender_ip: str):
        super().__init__(hex_data, sender_ip)

    def send_answer(self, result_code: int):
        try:
            ans_packet = bytes([0xFF, result_code])
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # logging.info(f"Попытка соединения с {self.sender_ip}:29789")
            sock.sendto(ans_packet, (self.sender_ip, 29789))
            sock.close()
            # logging.info(f"Отправлено подтверждение {ans_packet.hex()} на {self.sender_ip}")
        except Exception as e:
            # logging.error(f"Ошибка при отправке ответа: {e}")
            raise {'status': 'error', 'error_message': str(e)}

    def parse(self) -> Dict[str, Any]:
        try:
            parsed_data = {
                'dataType': self.__class__.__name__,
            }
            for field_name, field_type in self.structure:
                parsed_data[field_name] = self.read(field_type)

            count = parsed_data["count"]
            stations = {}

            for i in range(1, count + 1):
                station_id = self.read("int32")
                station_name = self.read("str")
                arrive_timestamp = self.read("int32")
                departure_timestamp = self.read("int32")

                stations[f"station{i}"] = {
                    f'stationName{i}': station_name,
                    f'stationID{i}': station_id,
                    f'arriveTimestamp{i}': dt.utcfromtimestamp(arrive_timestamp).strftime('%H:%M:%S'),
                    f'departureTimestamp{i}': dt.utcfromtimestamp(departure_timestamp).strftime('%H:%M:%S'),
                }

            parsed_data['stations'] = stations
            new_stops = get_stops_position(parsed_data)

            cached_stops = cache.get('cached_STOPS')

            if new_stops != cached_stops:
                logging.info('Обновляем stops, так как маршрут изменился.')
                cache_set("STOPS", new_stops)
                result_code = 0x00
            else:
                logging.info('Маршрут не изменился, stops остаётся тем же.')
                result_code = 0x00

            parsed_data['stops'] = new_stops
            del parsed_data['stations']

            self.send_answer(result_code)

            logging.info(f"Отработал класс RouteData")
            return parsed_data

        except Exception as e:
            logging.error(f"Ошибка в RouteData: {e}")
            self.send_answer(0x02)
            return {'status': 'error', 'error_message': str(e)}


class ConfigureData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("count", "int"),
    ]

    PORT_DEVICE_MAP = {
        1: 'БНТ (голова)',
        2: 'БНТ (торец)',
        3: 'БМВТ (голова)',
        4: 'БМВТ (торец)',
        5: 'БМВТ (мотор, голова)',
    }

    def __init__(self, hex_data: str, consumer: MoscowConsumer):
        super().__init__(hex_data)
        self.switch_ips = []
        self.consumer = consumer

    def parse(self) -> Dict[str, Any]:
        parsed_data = {
            'dataType': self.__class__.__name__,
        }
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        count = parsed_data["count"]
        for i in range(1, count + 1):
            raw_id = self.read("int32")
            parsed_data[f'id{i}_raw'] = raw_id

            id_data = self.decode_id(f'id{i}', raw_id)

            parsed_data.update(id_data)
            direction = self.read("byte")
            parsed_data[f'dir{i}'] = direction

            train = id_data[f"id{i}_train"]
            wagon = id_data[f"id{i}_wagon"]

            left_switch_ip = f"10.0.{train}.{wagon}"
            right_switch_ip = f"10.0.{train}.{wagon + 20}"

            if direction == 0x01:
                left_switch_ip, right_switch_ip = right_switch_ip, left_switch_ip

            self.switch_ips.append((train, wagon, left_switch_ip, right_switch_ip))

        logging.info(f"Карта коммутаторов: {self.switch_ips}")
        device_map = self.build_device_map()
        logging.info(f"Карта устройств: {device_map}")
        logging.info(f"Отработал класс ConfigureData")
        return parsed_data

    def build_device_map(self):
        device_map = {}

        for train, wagon, left_ip, right_ip in self.switch_ips:
            wagon_key = f'wagon_{wagon}'
            device_map[wagon_key] = {}

            for side, ip, in [('left_side', left_ip), ('right_side', right_ip)]:
                ports_info = self.get_ports_status(ip)
                if ports_info:
                    device_map[wagon_key][side] = ports_info

        logging.info(f"Карта устройств: {device_map}")

        return device_map

    def get_ports_status(self, switch_ip: str) -> dict:
        ports_statuses = {}

        connected_devices = self.consumer.query_switch(switch_ip)

        if not connected_devices:
            logging.warning(f"Коммутатор {switch_ip} не ответил, используем mock-данные")
            connected_devices = self.mock_devices()

        for port, device_info in connected_devices.items():
            device_ip = device_info['ip']
            device_type = self.PORT_DEVICE_MAP.get(port, 'Unknown device')
            status = device_info['status']

            ports_statuses[f"port_{port} ({device_type})"] = (device_ip, port, status)

        return ports_statuses

    @staticmethod
    def mock_devices() -> dict:
        return {
            1: {'ip': '192.168.1.101', 'status': 'connected'},
            2: {'ip': '192.168.1.102', 'status': 'disconnected'},
            3: {'ip': '192.168.1.103', 'status': 'connected'},
            4: {'ip': '192.168.1.104', 'status': 'disconnected'},
            5: {'ip': '192.168.1.105', 'status': 'connected'},
        }

    @staticmethod
    def decode_id(prefix: str, raw_id: int) -> Dict[str, int]:
        raw_id_str = f'{raw_id:09d}'
        return {
            f'{prefix}_type': int(raw_id_str[:4]),
            f'{prefix}_train': int(raw_id_str[4:7]),
            f'{prefix}_wagon': int(raw_id_str[7:]),
        }


class PacketFactory:

    PACKET_MAP = {
        '10': OperationalData,
        '11': AdditionalOperationalData,
        '20': RouteData,
        '31': ConfigureData,
    }

    @staticmethod
    def create_packet(data: bytes, sender_ip: str) -> ByteParserBase:
        packet_id = data[:2]
        packet_calss = PacketFactory.PACKET_MAP.get(packet_id)
        if not packet_calss:
            raise ValueError(f"Invalid packet id {packet_id}")

        # logging.info(f"Данные класса PacketFactory: {packet_calss}")
        if packet_calss == RouteData:
            return packet_calss(data[2:], sender_ip)
        else:
            return packet_calss(data[2:])


def cache_set(key, variable, timeout=86400):
    existing_value = cache.get(f"cached_{key}")
    if existing_value != variable:
        cache.set(f"cached_{key}", variable, timeout)

def cache_get(key: dict=None):
    if key is None:
        return {}
    return cache.get(f"cached_{key}")
