import struct
import logging
import binascii
import json
import asyncio

from channels.layers import get_channel_layer
from typing import List, Tuple, Dict, Any


class ByteParserBase:
    DATA_SIZE = {
        "int": 2,  # 2 символа HEX = 1 байт
        "float": 8,  # 8 символов HEX = 4 байта
        "int16": 4,  # 4 символа HEX = 2 байта
        "int32": 8,  # 8 символов HEX = 4 байта
        "byte": 2  # 2 символа HEX = 1 байт
    }

    def __init__(self, hex_data: str):
        self.data = hex_data
        self.offset = 0

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
        logging.info(f"Получена строка данных: {hex_data}")

        self.validate_marker()

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

    def parse_packet(self):
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

            payload = self.data[self.offset:]
            # logging.info(f"Полезная нагрузка: {payload}")

            if header['size'] > 0:
                payload_parser = PacketFactory.create_packet(payload)
                payload = payload_parser.parse_packet()

            parsed_data = {
                'header': header,
                'payload': payload,
                'status': 'success',
            }

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
            raise ValueError(f"Некорректный ID пакета: {packet_id}")


class OperationalData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("str", "str"),
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
        parsed_data = {}
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)
        logging.info(f"Данные класса OperationalData: {parsed_data}")
        return parsed_data


class AdditionalOperationalData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("outsideTemp", "int"),
        ("count", "int"),
    ]

    def parse(self) -> Dict[str, Any]:
        parsed_data = {}
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        count = parsed_data["count"]
        for i in range(1, count + 1):
            parsed_data[f'id{i}'] = self.read("int")
            parsed_data[f'train{i}'] = self.read("int")
            parsed_data[f'temp{i}'] = self.read("int")
            parsed_data[f'passengers{i}'] = self.read("int")

        logging.info(f"Данные класса AdditionalOperationalData: {parsed_data}")
        return parsed_data


class RouteData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("trainNumber", "str"),
        ("headSign", "str"),
        ("routeNumber", "int"),
        ("count", "int"),
    ]

    def parse(self) -> Dict[str, Any]:
        parsed_data = {}
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        count = parsed_data["count"]
        for i in range(1, count + 1):
            parsed_data[f'stationID{i}'] = self.read("float")
            parsed_data[f'stationName{i}'] = self.read("str")
            parsed_data[f'arriveTime{i}'] = self.read("float")
            parsed_data[f'departureTime{i}'] = self.read("float")

        logging.info(f"Данные класса RouteData: {parsed_data}")
        return parsed_data


class ConfigureData(ByteParserBase):
    structure: List[Tuple[str, str]] = [
        ("count", "int"),
    ]

    def parse(self) -> Dict[str, Any]:
        parsed_data = {}
        for field_name, field_type in self.structure:
            parsed_data[field_name] = self.read(field_type)

        count = parsed_data["count"]
        for i in range(1, count + 1):
            raw_id = self.read("int32")
            parsed_data[f'id{i}_raw'] = raw_id
            parsed_data.update(self.decode_id(f'id{i}', raw_id))
            parsed_data[f'dir{i}'] = self.read("byte")

        logging.info(f"Данные класса ConfigurelData: {parsed_data}")
        return parsed_data

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
    def create_packet(data: bytes) -> ByteParserBase:
        packet_id = data[:2]
        packet_calss = PacketFactory.PACKET_MAP.get(packet_id)
        if not packet_calss:
            raise ValueError(f"Invalid packet id {packet_id}")

        # logging.info(f"Данные класса PacketFactory: {packet_calss}")
        return packet_calss(data[2:])
