import json, os, base64
import xml.etree.ElementTree as ET
from json import JSONDecodeError

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.cache import cache


TREE = ET.parse('/home/andrew_q/PycharmProjects/TechTask/(bkl_fix)routes/L1/R2/BNT/1pt.bnt')
ROOT = TREE.getroot()

SW = None
SH = None

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


# d = get_stop_info(ROOT)
# print(d)
def index(request):
    global SW, SH
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            SW = data.get('screen_width')
            SH = data.get('screen_height')

            if SW == 1920 and SH == 1080:
                return JsonResponse({'redirect_url': 'BNT'})
            else:
                raise Exception
        except JSONDecodeError:
            return JsonResponse({'status': 'fail', 'message': 'Invalid JSON'}, status=400)
    return redirect('BNT')

def get_BNT(request):
    return render(request, 'Screen_Server/BNT.html')

def get_BNT_data():
    route = get_stop_info(ROOT)
    wagons_obj, wagons_obj_active = collect_wagons()
    if route['line']['isround'] == 'true':
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
            'wagons': wagons_obj,
            'wagons_active': wagons_obj_active,
        }
    else:
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
            'final_stop': route['stations'][-1],
            'wagons': wagons_obj,
            'wagons_active': wagons_obj_active,
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

    cache_timeout = 86400

    cache.set('current_station_index', next_station_index, timeout=cache_timeout)

    current_station_data = {
        'current_station': current_station,
        'next_station': next_station,
    }

    return current_station_data

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


def collect_wagons(size=8, side='Left'):
    wagons_dir = os.path.join(settings.BASE_DIR, 'Wagons/')
    wagons_obj = []
    wagons_obj_active = []

    for filename in os.listdir(wagons_dir):
        for i in range(1, size + 1):
            if f'Wagon {i} {side}-Side' in filename and 'Acitve' not in filename and filename.endswith('.png'):
                wagon_path = os.path.join(wagons_dir, filename)

                with open(wagon_path, 'rb') as wagon_file:
                    encoded_string = base64.b64encode(wagon_file.read())
                    wagon_obj = {'name': filename, 'encoded_string': encoded_string.decode('utf-8')}

                    wagons_obj.append(wagon_obj)

            elif f'Wagon {i} {side}-Side' in filename and 'Acitve' in filename and filename.endswith('.png'):
                wagon_path = os.path.join(wagons_dir, filename)

                with open(wagon_path, 'rb') as wagon_file:
                    encoded_string = base64.b64encode(wagon_file.read())
                    wagon_obj_active = {'name': filename, 'encoded_string': encoded_string.decode('utf-8')}

                    wagons_obj_active.append(wagon_obj_active)

    wagons_obj_active.sort(key=lambda x: x['name'], reverse=True)
    wagons_obj.sort(key=lambda x: x['name'], reverse=True)

    return wagons_obj, wagons_obj_active