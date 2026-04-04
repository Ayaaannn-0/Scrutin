from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import requests
import re

app = Flask(__name__)
CORS(app)

# ─── TRANSLATION MAP ─────────────
# Maps internal codenames to real-world hardware names
CHIPSET_MAP = {
    # --- THE "PARROT" FAMILY (Common in Motorola) ---
    "parrot": "Snapdragon 7s Gen 2 / 6 Gen 1", # Both chips use this codename
    "kodiak": "Snapdragon 6 Gen 1",           # Specific engineering name
    "monaco": "Snapdragon 6 Gen 3",           # The newer 2024/25 mid-range
    
    # --- QUALCOMM SNAPDRAGON (High-End) ---
    "sun": "Snapdragon 8 Elite",              # The brand new 2025 flagship
    "pineapple": "Snapdragon 8 Gen 3",
    "kalama": "Snapdragon 8 Gen 2",
    "taro": "Snapdragon 8 Gen 1",
    "lahaina": "Snapdragon 888",
    "kona": "Snapdragon 865",

    # --- QUALCOMM SNAPDRAGON (Mid-Range) ---
    "crow": "Snapdragon 7 Gen 3",
    "clipperton": "Snapdragon 7s Gen 3",
    "ponte": "Snapdragon 7 Gen 1",
    "sm6375": "Snapdragon 695",               # Very common in older Moto G series
    "bali": "Snapdragon 680",

    # --- GOOGLE TENSOR (Pixels) ---
    "zuma pro": "Tensor G4",
    "zuma": "Tensor G3",
    "cloudripper": "Tensor G2",
    "whitechapel": "Tensor G1",

    # --- SAMSUNG EXYNOS ---
    "s5e9945": "Exynos 2400",
    "s5e8845": "Exynos 1480",
    "s5e8835": "Exynos 1380",

    # --- MEDIATEK DIMENSITY ---
    "mt6991": "Dimensity 9400",
    "mt6989": "Dimensity 9300",
    "mt6877": "Dimensity 1080 / 7050",         # This is why AI got confused earlier
    "mt6833": "Dimensity 700"
}

# ─── ADB DATA EXTRACTION ──────────
def run_adb(command):
    try:
        result = subprocess.run(
            ['adb', 'shell', command],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"ADB Error ({command}):", e)
        return ""

def clean_model_name(brand, model):
    model = model.lower()
    brand = brand.lower()
    if model.startswith(brand):
        model = model.replace(brand, "").strip()
    return model

# ─── HARDWARE PARSERS ─────────────
def parse_battery(raw):
    data = {}
    for line in raw.splitlines():
        if 'level:' in line: data['level'] = line.split(':')[1].strip()
        if 'health:' in line: data['health'] = line.split(':')[1].strip()
        if 'temperature:' in line:
            temp = int(line.split(':')[1].strip())
            data['temperature'] = f"{temp / 10}°C"
        if 'voltage:' in line: data['voltage'] = f"{line.split(':')[1].strip()} mV"
        if 'technology:' in line: data['technology'] = line.split(':')[1].strip()
    
    health_map = {'1':'Unknown','2':'Good','3':'Overheat','4':'Dead','5':'Over Voltage','6':'Failure','7':'Cold'}
    if 'health' in data:
        data['health'] = health_map.get(data['health'], data['health'])
    if data.get('level') == '-1':
        data['level'] = 'N/A'
    
    return data

def parse_storage(raw):
    lines = raw.splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 4:
            total_gb = round(int(parts[1])/1024/1024, 1)
            return {
                'total': f"{total_gb} GB",
                'used' : f"{round(int(parts[2])/1024/1024, 1)} GB",
                'free' : f"{round(int(parts[3])/1024/1024, 1)} GB",
            }
    return {}

def parse_ram(raw):
    data = {}
    for line in raw.splitlines():
        if 'MemTotal:' in line:
            data['total'] = f"{round(int(line.split()[1])/1024/1024, 1)} GB"
        if 'MemAvailable:' in line:
            data['available'] = f"{round(int(line.split()[1])/1024/1024, 1)} GB"
    return data

# ─── COMPARISON ENGINE ────────────
def compare_hardware(scanned, official_string):
    """Compares scanned vs official and allows for system overhead."""
    if not official_string or official_string == 'N/A':
        return {"status": "unknown", "flag": "warn", "message": "No official data"}
    
    # 1. Exact string match (e.g., for chipsets or display)
    if str(scanned).lower() in str(official_string).lower():
        return {"status": "genuine", "flag": "ok", "message": "Match found"}

    # 2. Fuzzy number match (e.g., 7.2GB vs 8GB)
    s_nums = re.findall(r'\d+', str(scanned))
    o_nums = re.findall(r'\d+', str(official_string))
    
    if s_nums and o_nums:
        s_val = int(s_nums[0])
        # Check if scanned value is at least 80% of any official variant
        for o_val in [int(n) for n in o_nums]:
            if s_val >= (o_val * 0.8) and s_val <= (o_val * 1.1):
                return {"status": "genuine", "flag": "ok", "message": "Match found"}
            
    return {"status": "suspicious", "flag": "danger", "message": f"Mismatch: {scanned} vs {official_string}"}


def mark_comparison_uncertain(comp, reason):
    if comp.get("flag") == "danger":
        return {
            "status": "unknown",
            "flag": "warn",
            "message": f"Variant uncertain ({reason})",
        }
    return comp

# ─── MAIN SCAN ROUTE ──────────────
@app.route('/scan')
def scan():
    # 1. Physical Extraction
    brand = run_adb('getprop ro.product.brand').capitalize()
    raw_model = run_adb('getprop ro.product.model')
    model = clean_model_name(brand, raw_model)
    
    android = run_adb('getprop ro.build.version.release')
    chipset_raw = run_adb('getprop ro.board.platform')
    # Translate "parrot" -> "Snapdragon 7s Gen 2"
    readable_chipset = CHIPSET_MAP.get(chipset_raw.lower(), chipset_raw)
    
    resolution = run_adb('wm size').replace('Physical size: ', '')
    battery = parse_battery(run_adb('dumpsys battery'))
    storage = parse_storage(run_adb('df /data'))
    ram = parse_ram(run_adb('cat /proc/meminfo'))

    # 2. Official specification lookup
    official = None
    try:
        from specs import get_official_specs
        print(
            f"Calling get_official_specs with: {brand.lower()} | {model} | "
            f"{ram.get('total')} | {storage.get('total')}"
        )
        official = get_official_specs(
            brand.lower(),
            model,
            scanned_ram=ram.get('total', None),
            scanned_storage=storage.get('total', None)
        )
    except Exception as e:
        print(f"❌ get_official_specs failed: {e}")

    # 3. Dynamic Comparison and Trust Scoring
    comparisons = {}
    score = 10
    
    if official:
        comparisons["display"] = compare_hardware(resolution, official.get('display'))
        comparisons["ram"] = compare_hardware(ram.get('total'), official.get('ram'))
        comparisons["storage"] = compare_hardware(storage.get('total'), official.get('storage'))
        comparisons["chipset"] = compare_hardware(readable_chipset, official.get('chipset'))

        variant_conf = official.get("variant_confidence", "high")
        variant_reason = official.get("variant_reason", "no reason")
        if variant_conf == "low":
            for key in ("ram", "storage", "chipset"):
                comparisons[key] = mark_comparison_uncertain(comparisons[key], variant_reason)
        
        for comp in comparisons.values():
            if comp["flag"] == "danger": score -= 2
            elif comp["flag"] == "warn": score -= 0.5

    return jsonify({
        "device": {
            "brand": brand,
            "model": raw_model,
            "android": android,
            "chipset": readable_chipset,
            "codename": chipset_raw
        },
        "battery": battery,
        "display": {"resolution": resolution},
        "ram": ram,
        "storage": storage,
        "official": official,
        "comparisons": comparisons,
        "trust_score": max(0, round(score))
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)