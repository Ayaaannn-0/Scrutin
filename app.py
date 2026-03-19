from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)

# ─── ADB ────────────────────────────────────────────
def run_adb(command):
    result = subprocess.run(
        ['adb', 'shell', command],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def parse_battery(raw):
    data = {}
    for line in raw.splitlines():
        if 'level:' in line:
            data['level'] = line.split(':')[1].strip()
        if 'health:' in line:
            data['health'] = line.split(':')[1].strip()
        if 'temperature:' in line:
            temp = int(line.split(':')[1].strip())
            data['temperature'] = str(temp / 10) + '°C'
        if 'voltage:' in line:
            data['voltage'] = line.split(':')[1].strip() + ' mV'
        if 'technology:' in line:
            data['technology'] = line.split(':')[1].strip()
    return data

def parse_health(code):
    health_codes = {
        '1': 'Unknown',
        '2': 'Good',
        '3': 'Overheat',
        '4': 'Dead',
        '5': 'Over Voltage',
        '6': 'Unspecified Failure',
        '7': 'Cold'
    }
    return health_codes.get(code, 'Unknown')

def parse_storage(raw):
    lines = raw.splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        total_gb = round(int(parts[1]) / 1024 / 1024, 1)
        used_gb  = round(int(parts[2]) / 1024 / 1024, 1)
        free_gb  = round(int(parts[3]) / 1024 / 1024, 1)
        return {
            'total': str(total_gb) + ' GB',
            'used' : str(used_gb)  + ' GB',
            'free' : str(free_gb)  + ' GB',
        }
    return {}

def parse_ram(raw):
    data = {}
    for line in raw.splitlines():
        if 'MemTotal:' in line:
            kb = int(line.split()[1])
            data['total'] = str(round(kb / 1024 / 1024, 1)) + ' GB'
        if 'MemAvailable:' in line:
            kb = int(line.split()[1])
            data['available'] = str(round(kb / 1024 / 1024, 1)) + ' GB'
    return data

# ─── COMPARISON LOGIC ───────────────────────────────
def compare_chipset(scanned, official):
    # Extract key part of chipset for comparison
    scanned  = scanned.lower()
    official = official.lower()
    if 'mt6785' in scanned and 'mt6785' in official:
        return {'status': 'genuine', 'flag': 'ok', 'message': 'Chipset matches official spec'}
    elif 'mt6785' in scanned or 'mt6785' in official:
        return {'status': 'suspicious', 'flag': 'warn', 'message': 'Chipset partially matches'}
    elif scanned in official or official in scanned:
        return {'status': 'genuine', 'flag': 'ok', 'message': 'Chipset matches official spec'}
    else:
        return {'status': 'fake', 'flag': 'danger', 'message': 'Chipset does not match official spec'}

def compare_display(scanned, official):
    # Extract resolution numbers
    scanned_res  = scanned.replace('x', '').replace(' ', '')
    official_res = official.replace('x', '').replace(' ', '').replace(',', '')
    if scanned.replace('x','') in official.replace('x',''):
        return {'status': 'genuine', 'flag': 'ok', 'message': 'Display resolution matches'}
    else:
        return {'status': 'fake', 'flag': 'danger', 'message': 'Display resolution does not match'}

def compare_ram(scanned_gb, official_str):
    # official_str like "8GB RAM", scanned_gb like 7.4
    try:
        official_gb = float(official_str.lower().replace('gb ram', '').replace('gb', '').strip())
        diff = abs(official_gb - scanned_gb)
        if diff <= 0.5:
            return {'status': 'genuine', 'flag': 'ok', 'message': 'RAM matches official spec'}
        else:
            return {'status': 'suspicious', 'flag': 'warn', 'message': f'RAM differs — expected {official_gb}GB'}
    except:
        return {'status': 'unknown', 'flag': 'warn', 'message': 'Could not compare RAM'}

# ─── ROUTES ─────────────────────────────────────────
@app.route('/')
def home():
    return 'Scrutin is running!'

@app.route('/scan')
def scan():
    # Pull real data from phone via ADB
    brand   = run_adb('getprop ro.product.brand').capitalize()
    model   = run_adb('getprop ro.product.model')
    android = run_adb('getprop ro.build.version.release')
    chipset = run_adb('getprop ro.board.platform')

    battery_raw = run_adb('dumpsys battery')
    battery     = parse_battery(battery_raw)
    storage     = parse_storage(run_adb('df /data'))
    ram         = parse_ram(run_adb('cat /proc/meminfo'))
    resolution  = run_adb('wm size').replace('Physical size: ', '')

    # Get official specs from GSMArena
    from gsmarena import get_official_specs
    official = get_official_specs(brand.lower(), model)

    # Build comparison results
    comparisons = {}
    if official:
        comparisons['chipset'] = compare_chipset(chipset, official.get('chipset', ''))
        comparisons['display'] = compare_display(resolution, official.get('display', ''))
        ram_total = float(ram.get('total', '0').replace(' GB', ''))
        comparisons['ram']     = compare_ram(ram_total, official.get('ram', ''))

    # Calculate trust score
    flags = [c['flag'] for c in comparisons.values()]
    score = 10
    for flag in flags:
        if flag == 'danger': score -= 3
        if flag == 'warn':   score -= 1
    score = max(0, score)

    return jsonify({
        'device': {
            'brand'     : brand,
            'model'     : model,
            'android'   : android,
            'chipset'   : chipset,
        },
        'display': {
            'resolution': resolution,
        },
        'battery': {
            'level'      : battery.get('level', 'N/A'),
            'health'     : parse_health(battery.get('health', '1')),
            'temperature': battery.get('temperature', 'N/A'),
            'voltage'    : battery.get('voltage', 'N/A'),
            'technology' : battery.get('technology', 'N/A'),
        },
        'storage' : storage,
        'ram'     : ram,
        'official': official,
        'comparisons': comparisons,
        'trust_score': score,
    })

if __name__ == '__main__':
    app.run(debug=True)