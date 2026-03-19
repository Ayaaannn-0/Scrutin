import requests
import json
import os
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

CACHE_FILE = 'specs_cache.json'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_gsmarena_url(brand, model):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""What is the exact GSMArena.com URL for {brand} phone with model number {model}?
            Reply with ONLY the URL like: https://www.gsmarena.com/vivo_y73-11022.php
            Nothing else. Just the URL."""
        }]
    )
    url = response.choices[0].message.content.strip()
    if 'gsmarena.com' in url and '.php' in url:
        return url
    return None

def scrape_gsmarena(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    raw = {}
    rows = soup.select('tr')
    for row in rows:
        header = row.select_one('.ttl')
        value  = row.select_one('.nfo')
        if header and value:
            raw[header.text.strip()] = value.text.strip()

    # Parse RAM and storage from Internal field
    internal = raw.get('Internal', '')
    storage = 'N/A'
    ram = 'N/A'
    if internal:
        parts = internal.split()
        for i, part in enumerate(parts):
            if 'GB' in part and i+1 < len(parts) and parts[i+1] == 'RAM':
                ram = part + ' RAM'
            elif 'GB' in part and i > 0 and parts[i-1] != 'RAM':
                storage = part

    return {
        'battery' : raw.get('Type', 'N/A'),
        'chipset' : raw.get('Chipset', 'N/A'),
        'display' : raw.get('Resolution', 'N/A'),
        'ram'     : ram,
        'storage' : storage,
        'os'      : raw.get('OS', 'N/A'),
        'size'    : raw.get('Size', 'N/A'),
    }

def get_official_specs(brand, model):
    cache_key = f"{brand}_{model}".lower()
    cache = load_cache()

    # Return cached version if available
    if cache_key in cache:
        print(f"✅ Loaded from cache: {brand} {model}")
        return cache[cache_key]

    print(f"🔍 Searching GSMArena URL for {brand} {model}...")
    url = get_gsmarena_url(brand, model)

    if not url:
        print("❌ Could not find GSMArena URL")
        return None

    print(f"📡 Fetching specs from: {url}")
    specs = scrape_gsmarena(url)

    # Save to cache
    cache[cache_key] = specs
    save_cache(cache)
    print(f"💾 Saved to cache")

    return specs

# Test
if __name__ == '__main__':
    specs = get_official_specs('vivo', 'V2059')
    if specs:
        print()
        for key, val in specs.items():
            print(f"{key:12} : {val}")
