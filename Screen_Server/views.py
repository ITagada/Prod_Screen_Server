import json
import xml.etree.ElementTree as ET
from json import JSONDecodeError

from django.shortcuts import render, redirect
from django.http import JsonResponse


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


d = get_stop_info(ROOT)
print(d)
# print(d['line']['isround'])

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
    if route['line']['isround'] == 'true':
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
        }
    else:
        context = {
            'line_name': route['line']['name'],
            'line_name2': route['line']['name2'],
            'line_icons': route['line']['icons'],
            'stops': route['stations'],
            'final_stop': route['stations'][-1],
        }
    return context

