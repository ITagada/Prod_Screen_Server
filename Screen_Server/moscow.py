import struct

from typing import List, Tuple, Dict, Any


class SessionProtocolParser:
    HEADER_FORMAT = "<I4s4sHcH2s"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def parse_header(self) -> Dict[str, Any]:
        if len(self.data) < self.HEADER_SIZE:
            raise ValueError(f"Data size ({len(self.data)}) is less than header size ({self.HEADER_SIZE})")

        header_data = struct.unpack_from(self.HEADER_FORMAT, self.data, self.offset)
        self.offset += self.HEADER_SIZE

        header = {
            "mark": header_data[0],
            "to": header_data[1],
            "from": header_data[2],
            "id": header_data[3],
            "minor_version": header_data[4],
            "size": header_data[5],
            "cs": int.from_bytes(header_data[6], byteorder="big"),
        }

        if header["mark"] != 0xFFA00010:
            raise ValueError(f"Invalid mark: {header['mark']}")

        if not self.validate_checksum(header["cs"]):
            raise ValueError("Checksum validation failed")

        return header

    def validate_checksum(self, cs: int) -> bool:
        calculated_cs = sum(self.data[:-2]) & 0xFFFF
        return calculated_cs == cs

    def parse_packet(self) -> Dict[str, Any]:
        header = self.parse_header()

        if self.offset + header["size"] > len(self.data):
            raise ValueError(f"Data size ({len(self.data)}) is less than expected size ({self.offset + header['size']})")

        packet_data = self.data[self.offset:self.offset + header["size"]]
        self.offset += header["size"]

        packet = PacketFactory.create_packet(packet_data)
        return {
            "header": header,
            "payload": packet.parse(),
        }


class ByteParserBase:

    DATA_SIZE = {
        "int": 1,
        "float": 4,
        "int16": 2,
        "int32": 4,
        "byte": 1
    }

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read(self, data_type: str) -> Any:
        if data_type == "str":
            if self.offset + 2 > len(self.data):
                raise ValueError(f"Not enough data for string length at offset {self.offset}")

            # Просмотр байтов для длины строки
            length_bytes = self.data[self.offset:self.offset + 2]

            # Количество байт в строке (не длина в символах)
            str_byte_length = int.from_bytes(length_bytes, byteorder="big")

            self.offset += 2

            # Проверка, достаточно ли данных
            if self.offset + str_byte_length > len(self.data):
                raise ValueError(
                    f"String byte length ({str_byte_length}) exceeds data size at offset {self.offset} "
                    f"(data length={len(self.data)})"
                )

            # Чтение строки
            try:
                value = self.data[self.offset:self.offset + str_byte_length].decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError(f"Failed to decode string at offset {self.offset}: {e}")

            self.offset += str_byte_length
            return value

        size = self.DATA_SIZE.get(data_type)
        if not size:
            raise ValueError(f"Invalid data type {data_type}")

        if data_type == "byte":
            value = self.data[self.offset]
            self.offset += size
            return value

        if data_type == "float":
            value = struct.unpack_from(">f", self.data, self.offset)[0]
            self.offset += size
            return value

        if data_type == "int32":
            # Используем struct для распаковки с правильным порядком байтов
            value = struct.unpack_from(">I", self.data, self.offset)[0]  # <I - little-endian unsigned int
            self.offset += size
            return value

        if data_type in ("int", "int16"):
            # Для маленьких значений
            if data_type == "int16":
                value = struct.unpack_from("<h", self.data, self.offset)[0]  # <h - little-endian short (signed)
            else:
                value = struct.unpack_from("<b", self.data, self.offset)[0]  # <i - little-endian int (signed)
            self.offset += size
            return value

        raise ValueError(f"Invalid data type {data_type}")


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
        0x10: OperationalData,
        0x11: AdditionalOperationalData,
        0x20: RouteData,
        0x31: ConfigureData,
    }

    @staticmethod
    def create_packet(data: bytes) -> ByteParserBase:
        packet_id = data[0]
        packet_calss = PacketFactory.PACKET_MAP.get(packet_id)
        if not packet_calss:
            raise ValueError(f"Invalid packet id {packet_id}")
        return packet_calss(data[1:])


# ДЛЯ OperationalData
# raw_data = (
#     b'\x10'  # ID пакета (byte)
#     b'\x00\x08time_test'  # str (длина 8, строка "time_test")
#     b'\x42\x48\x96\x49'  # float (latitude)
#     b'\xc2\x48\x96\x49'  # float (longitude)
#     b'\x00\x32'  # int (speed)
#     b'\x01'  # byte (mode)
#     b'\x00\x00\x03\xe8'  # int32 (nextStationID)
#     b'\x00\x00\x07\xd0'  # int32 (nextStationDistance)
#     b'\x01'  # byte (nextStationSide)
#     b'\x00\x03'  # int (nextStationPathNum)
#     b'\x02'  # byte (doorState)
# )

# ДЛЯ AdditionalOperationalData
# raw_data = (
#     b'\x11'  # ID пакета (byte)
#     b'\x15'  # outsideTemp (int)
#     b'\x02'  # count (int) - 2 записи
#     b'\x01'  # id1 (int)
#     b'\x0A'  # train1 (int)
#     b'\x14'  # temp1 (int)
#     b'\x1E'  # passengers1 (int)
#     b'\x02'  # id2 (int)
#     b'\x0B'  # train2 (int)
#     b'\x15'  # temp2 (int)
#     b'\x1F'  # passengers2 (int)
# )

# ДЛЯ RouteData
# raw_data = (
#     b'\x20'  # ID пакета (RouteData)
#     b'\x00\x09'  # trainNumber (длина в байтах: 9)
#     b'Train-123'  # trainNumber
#     b'\x00\x08'  # headSign (длина в байтах: 8)
#     b'HeadSign'  # headSign
#     b'\x03'  # routeNumber
#     b'\x05'  # count (количество станций)
#     b'\x41\xA0\x00\x00'  # stationID1
#     b'\x00\x09Station-1'  # stationName1
#     b'\x41\xC8\x00\x00'  # arriveTime1
#     b'\x41\xD0\x00\x00'  # departureTime1
#     b'\x41\xA8\x00\x00'  # stationID2
#     b'\x00\x09Station-2'  # stationName2
#     b'\x41\xD8\x00\x00'  # arriveTime2
#     b'\x41\xE0\x00\x00'  # departureTime2
#     b'\x41\xB0\x00\x00'  # stationID3
#     b'\x00\x09Station-3'  # stationName3
#     b'\x41\xE8\x00\x00'  # arriveTime3
#     b'\x41\xF0\x00\x00'  # departureTime3
#     b'\x41\xB8\x00\x00'  # stationID4
#     b'\x00\x09Station-4'  # stationName4
#     b'\x41\xF8\x00\x00'  # arriveTime4
#     b'\x42\x00\x00\x00'  # departureTime4
#     b'\x41\xC0\x00\x00'  # stationID5
#     b'\x00\x09Station-5'  # stationName5
#     b'\x42\x08\x00\x00'  # arriveTime5
#     b'\x42\x10\x00\x00'  # departureTime5
# )

import sys

# ДЛЯ ConfigureData
raw_data = (
    b'\x31'
    b'\x04'
    b'\x07\x5b\xcd\x15'
    b'\x00'
    b'\x3a\xde\x68\xb1'
    b'\x01'
    b'\x28\xce\x61\x61'
    b'\x00'
    b'\x3a\x15\xe4\x0c'
    b'\x01'
)

# Создание пакета и его парсинг
packet = PacketFactory.create_packet(raw_data)
parsed_data = packet.parse()
print(parsed_data)