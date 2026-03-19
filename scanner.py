import subprocess


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
        total_kb = int(parts[1])
        used_kb  = int(parts[2])
        free_kb  = int(parts[3])
        total_gb = round(total_kb / 1024 / 1024, 1)
        used_gb  = round(used_kb  / 1024 / 1024, 1)
        free_gb  = round(free_kb  / 1024 / 1024, 1)
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

def parse_resolution(raw):
    return raw.replace('Physical size: ', '')

# Pull data
brand      = run_adb('getprop ro.product.brand')
model      = run_adb('getprop ro.product.model')
android    = run_adb('getprop ro.build.version.release')
chipset    = run_adb('getprop ro.board.platform')
resolution = parse_resolution(run_adb('wm size'))

battery = parse_battery(run_adb('dumpsys battery'))
storage = parse_storage(run_adb('df /data'))
ram     = parse_ram(run_adb('cat /proc/meminfo'))

# Print results
print()
print("╔══════════════════════════════╗")
print("║        SCRUTIN  SCAN         ║")
print("╚══════════════════════════════╝")
print()
print("─── Device ───────────────────")
print(f"  Brand      : {brand.capitalize()}")
print(f"  Model      : {model}")
print(f"  Android    : {android}")
print(f"  Chipset    : {chipset}")
print()
print("─── Display ──────────────────")
print(f"  Resolution : {resolution}")
print()
print("─── Battery ──────────────────")
print(f"  Level      : {battery.get('level', 'N/A')}%")
print(f"  Health     : {parse_health(battery.get('health', '1'))}")
print(f"  Temperature: {battery.get('temperature', 'N/A')}")
print(f"  Voltage    : {battery.get('voltage', 'N/A')}")
print(f"  Technology : {battery.get('technology', 'N/A')}")
print()
print("─── Storage ──────────────────")
print(f"  Total      : {storage.get('total', 'N/A')}")
print(f"  Used       : {storage.get('used', 'N/A')}")
print(f"  Free       : {storage.get('free', 'N/A')}")
print()
print("─── RAM ──────────────────────")
print(f"  Total      : {ram.get('total', 'N/A')}")
print(f"  Available  : {ram.get('available', 'N/A')}")
print()
print("══════════════════════════════")