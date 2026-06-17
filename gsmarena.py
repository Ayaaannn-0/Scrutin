import requests
import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
MOBILE_API_KEY = os.getenv('MOBILE_API_KEY')

CACHE_FILE     = 'specs_cache.json'


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def parse_specs(device):
    result = {'battery':'N/A','chipset':'N/A','display':'N/A','ram':'N/A','storage':'N/A'}
    hw_str  = device.get('hardware', '')
    bat     = device.get('battery_capacity', '')
    res_str = device.get('screen_resolution', '')
    sto     = device.get('storage', '')
    if bat:
        result['battery'] = bat
    if res_str:
        res_match = re.search(r'(\d+x\d+)', res_str)
        if res_match:
            result['display'] = res_match.group(1)
    if sto:
        result['storage'] = sto
    if hw_str:
        ram_match = re.search(r'(\d+(?:/\d+)?GB)\s*RAM', hw_str, re.IGNORECASE)
        if ram_match:
            result['ram'] = ram_match.group(1).split('/')[-1] + ' RAM'
        parts = hw_str.split(',')
        if len(parts) >= 2:
            result['chipset'] = parts[-1].strip()
    return result

def check_match(scanned, official):
    if not scanned or not official or official == 'N/A':
        return False
    scanned_nums  = re.findall(r'\d+', str(scanned))
    official_nums = re.findall(r'\d+', str(official))
    if not scanned_nums or not official_nums:
        return False
    s_val = int(scanned_nums[0])
    for o_val in [int(n) for n in official_nums]:
        if abs(s_val - o_val) <= 2:
            return True
    return False

def get_official_specs(brand, model, scanned_ram=None, scanned_storage=None):
    cache_key = f"{brand}_{model}".lower()
    cache     = load_cache()

    if cache_key in cache:
        print(f"✅ Loaded from cache: {brand} {model}")
        return cache[cache_key]

    print(f"API Key loaded: {MOBILE_API_KEY[:8] if MOBILE_API_KEY else 'NONE'}")

    queries = [
    'edge 50 fusion',                        # Short — no brand
    model.replace('motorola', '').strip(),   # Remove brand from model
    model,                                   # Full model name
]
    

    for query in queries:
        print(f"🔍 Searching MobileAPI: {query}")
        try:
            response = requests.get(
                "https://api.mobileapi.dev/devices/search",
                params={"name": query, "key": MOBILE_API_KEY},
                timeout=10
            )
            data    = response.json()
            devices = data.get('devices', [])
            total   = data.get('total', 0)
            print(f"   Found {total} results")

            if not devices:
                continue

            best_phone = None
            best_specs = None

            for device in devices[:5]:
                parsed = parse_specs(device)
                name   = device.get('name', '')
                print(f"   Checking: {name} — RAM: {parsed.get('ram')} Storage: {parsed.get('storage')}")

                if scanned_ram and scanned_storage:
                    ram_ok = check_match(scanned_ram, parsed.get('ram', ''))
                    sto_ok = check_match(scanned_storage, parsed.get('storage', ''))
                    if ram_ok and sto_ok:
                        print(f"✅ Exact variant match: {name}")
                        best_phone = device
                        best_specs = parsed
                        break

                if not best_specs:
                    best_phone = device
                    best_specs = parsed

            if best_specs:
                # Check if we actually got useful data
                all_na = all(v == 'N/A' for v in best_specs.values())
                if all_na:
                    print("⚠️ All specs are N/A — trying Groq fallback...")
                    try:
                        from specs import get_official_specs as groq_specs
                        groq_result = groq_specs(brand, model, scanned_ram, scanned_storage)
                        if groq_result:
                            cache[cache_key] = groq_result
                            save_cache(cache)
                            return groq_result
                    except Exception as e:
                        print(f"Groq fallback failed: {e}")

                print(f"📱 Using: {best_phone.get('name')}")
                cache[cache_key] = best_specs
                save_cache(cache)
                print("💾 Saved to cache")
                return best_specs

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    print("❌ Could not find specs")
    return None
