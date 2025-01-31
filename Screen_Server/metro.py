import json, os, base64
import xml.etree.ElementTree as ET

from json import JSONDecodeError
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer, channel_layers

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.cache import cache


file_path = os.path.join(settings.BASE_DIR, 'L1', 'R2', 'BNT', '1pt.bnt')
TREE = ET.parse(file_path)
ROOT = TREE.getroot()

SW = None
SH = None

CURRENT_STATION_INDEX = 0

CLIENTS_IP = []


class Client:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.wagon_number, self.side = self._determine_parametrs()

    def _determine_parametrs(self):
        last_octet = int(self.ip_address.split('.')[-1])
        wagon_number = last_octet // 10
        side = 'Left' if last_octet % 2 == 0 else 'Right'
        return wagon_number, side

    def get_client_attr(self):
        return {
            'ip_address': self.ip_address,
            'wagon_number': self.wagon_number,
            'side': self.side,
        }


def parse_station(station):
    transfers = []
    for transfer in station.findall('transfer'):
        icon_parts = [
            {'color': iconpart.get('color'),
             'symbol': iconpart.get('symbol'),
             }
            for iconpart in transfer.find('icon').findall('iconpart')
        ]
        transfers.append({
            'transfer_name': transfer.get('name').split('|')[0],
            'transfer_name2': transfer.get('name').split('|')[1],
            'isshow': transfer.get('isShow'),
            'icon_parts': icon_parts,
        })

    return {
        'name': station.get('name').split('|')[0],
        'name2': station.get('name').split('|')[1],
        'side': station.get('side'),
        'up': station.get('up'),
        'skip': station.get('skip'),
        'pos': station.get('pos'),
        'cityexit': station.get('cityexit'),
        'metro_transfer': station.get('metro_transfer'),
        'crossplatform': station.get('crossPlatform'),
        'transfers': transfers,
    }

def get_stop_info(ROOT):
    stations = []

    for station in ROOT.findall('station'):
        stations.append(parse_station(station))

    line_icons = []
    line_icons_element = ROOT.find('icon')
    if line_icons_element is not None:
        for iconpart in ROOT.find('icon').findall('iconpart'):
            line_icons.append({
                'color': iconpart.get('color'),
                'symbol': iconpart.get('symbol'),
            })

    route = {
        'line': {
            'name': ROOT.get('name').split('|')[0],
            'name2': ROOT.get('name').split('|')[1],
            'isround': ROOT.get('isround'),
            'icons': line_icons,
        },
        'stations': stations,
    }

    return route

# def index(request):
#     global SW, SH
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             SW = data.get('screen_width')
#             SH = data.get('screen_height')
#
#             if SW == 1920 and SH == 1080:
#                 return JsonResponse({'redirect_url': 'BNT'})
#             else:
#                 raise Exception
#         except JSONDecodeError:
#             return JsonResponse({'status': 'fail', 'message': 'Invalid JSON'}, status=400)
#     return redirect('BNT')

def get_BNT(request):
    ip_address = get_clietnt_ip(request)
    if ip_address not in CLIENTS_IP:
        CLIENTS_IP.append(ip_address)
    return render(request, 'Screen_Server/BNT.html')

def get_clietnt_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_BNT_data(client_ip):
    route = get_stop_info(ROOT)
    client = Client(client_ip)
    wagons_obj = collect_wagons(size=8, side=client.side, current_wagon=client.wagon_number)
    if route['line']['isround'] == 'true':
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
            'side': client.side,
            'wagons': wagons_obj,
        }
    else:
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
            'final_stop': route['stations'][-1],
            'side': client.side,
            'wagons': wagons_obj,
        }

    return context

def update_route():
    route = get_stop_info(ROOT)
    stations = route['stations']

    current_station_index = cache.get('current_station_index', 0)

    if route['line']['isround'] == 'true':
        if current_station_index == len(stations) - 1:
            next_station_index = 0
        else:
            next_station_index = current_station_index + 1
    elif current_station_index < (len(stations) - 1):
        next_station_index = current_station_index + 1
    else:
        route['stations'].reverse()
        next_station_index = 0

    current_station = stations[current_station_index]
    next_station = stations[next_station_index]

    current_params = get_station_config(current_station_index + 1)

    current_png = format_image(current_params["PNG"]) if current_params["PNG"] else None

    cache_timeout = 86400

    cache.set('current_station_index', next_station_index, timeout=cache_timeout)

    current_station_data = {
        'current_station': current_station,
        'next_station': next_station,
        'current_png': current_png,
    }

    return current_station_data

def get_station_config(station_index, is_reverse=False):
    folder_name = f"{station_index}o" if is_reverse else str(station_index)
    station_config_path = os.path.join(settings.BASE_DIR, 'L1', 'R2', 'Way 1', folder_name, 'config.ini')

    config_data = {}
    try:
        with open(station_config_path, 'r') as file:
            for line in file:
                # Пропускаем пустые строки
                line = line.strip()
                if line:
                    # Убираем точку с запятой, разделяем по ": " и записываем результат в config_data
                    key, value = line.replace(';', '').split(': ')
                    config_data[key.strip()] = value.strip()
    except FileNotFoundError:
        return {'PNG': None}

    # Получаем значение PNG, если оно есть
    png_value = config_data.get('PNG', None)

    return {'PNG': png_value}

def format_image(image_name):
    image_path = os.path.join(settings.BASE_DIR, 'L1', 'R2', 'PNG', image_name)
    try:
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def send_current_route_data():
    station_data = update_route()
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        'route_updates',
        {
            'type': 'update_station',
            'message': station_data,
        }
    )


def collect_wagons(size=8, side='Left', current_wagon = 1):
    wagons_dir = os.path.join(settings.BASE_DIR, 'Wagons/')
    wagons_obj = []

    for filename in os.listdir(wagons_dir):
        for i in range(1, size + 1):
            if f'Wagon {i} {side}-Side' in filename and 'Acitve' not in filename and filename.endswith('.png') and i != current_wagon:
                wagon_path = os.path.join(wagons_dir, filename)

                with open(wagon_path, 'rb') as wagon_file:
                    encoded_string = base64.b64encode(wagon_file.read())
                    wagon_obj = {'name': filename, 'encoded_string': encoded_string.decode('utf-8')}

                    wagons_obj.append(wagon_obj)

            elif f'Wagon {i} {side}-Side' in filename and 'Acitve' in filename and filename.endswith('.png') and i == current_wagon:
                wagon_path = os.path.join(wagons_dir, filename)

                with open(wagon_path, 'rb') as wagon_file:
                    encoded_string = base64.b64encode(wagon_file.read())
                    wagon_obj = {'name': filename, 'encoded_string': encoded_string.decode('utf-8')}

                    wagons_obj.append(wagon_obj)

    wagons_obj.sort(key=lambda x: x['name'])

    return wagons_obj
