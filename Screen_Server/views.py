import xml.etree.ElementTree as ET


from django.shortcuts import render


tree = ET.parse('/home/andrew_q/PycharmProjects/TechTask/(bkl_fix)routes/L1/R2/BNT/1pt.bnt')
root = tree.getroot()

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
            'transfer_name': transfer.get('name'),
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

def get_stop_info(root):
    stations = []

    for station in root.findall('station'):
        stations.append(parse_station(station))

    line = {
        'line': {
            'name': root.get('name').split('|')[0],
            'name2': root.get('name').split('|')[1],
            'isround': root.get('isround'),
        },
        'stations': stations,
    }

    return line

print(get_stop_info(root))

def index(request):
    return render(request, 'Screen_Server/index.html')
# Create your views here.
