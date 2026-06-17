import json
import os
import re

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CACHE_FILE = "specs_cache.json"
FEATHERLESS_MODEL = "Qwen/Qwen2.5-72B-Instruct"
NA_SPECS = {
    "battery": "N/A",
    "chipset": "N/A",
    "display": "N/A",
    "ram": "N/A",
    "storage": "N/A",
    "overhead": 0.25,
    "source": "none",
}

HARDWARE_SYNONYMS = {
    # ── Qualcomm Snapdragon: codenames & model numbers ──
    "parrot": ["snapdragon", "6 gen 1", "7s gen 2", "sm6450", "sm7435"],
    "sm6450": ["snapdragon", "6 gen 1", "parrot"],
    "sm7435": ["snapdragon", "7s gen 2", "parrot"],
    "bengal": ["snapdragon", "680", "662", "khaje"],
    "khaje": ["snapdragon", "680", "bengal"],
    "taro": ["snapdragon", "8 gen 1", "sm8450"],
    "sm8450": ["snapdragon", "8 gen 1", "taro"],
    "cape": ["snapdragon", "8+ gen 1", "sm8475"],
    "sm8475": ["snapdragon", "8+ gen 1", "cape"],
    "kalama": ["snapdragon", "8 gen 2", "sm8550"],
    "sm8550": ["snapdragon", "8 gen 2", "kalama"],
    "pineapple": ["snapdragon", "8 gen 3", "sm8650"],
    "sm8650": ["snapdragon", "8 gen 3", "pineapple"],
    "sun": ["snapdragon", "8 elite", "8 gen 4", "sm8750"],
    "sm8750": ["snapdragon", "8 elite", "8 gen 4", "sun"],
    "lahaina": ["snapdragon", "888", "sm8350"],
    "sm8350": ["snapdragon", "888", "lahaina"],
    "lito": ["snapdragon", "765g", "765", "sm7250"],
    "sm7250": ["snapdragon", "765g", "765", "lito"],
    "yupik": ["snapdragon", "778g", "778g+", "sm7325"],
    "sm7325": ["snapdragon", "778g", "778g+", "yupik"],
    "sm6375": ["snapdragon", "695"],
    "holi": ["snapdragon", "480", "4 gen 1", "sm6375"],
    "crow": ["snapdragon", "7 gen 1", "sm7450"],
    "sm7450": ["snapdragon", "7 gen 1", "crow"],
    "sm7475": ["snapdragon", "7+ gen 2"],
    "sm6225": ["snapdragon", "680", "685"],
    "trinket": ["snapdragon", "665"],
    "atoll": ["snapdragon", "720g"],
    # ── MediaTek Helio & Dimensity ──
    "mt6765": ["helio", "g35", "g25", "p35"],
    "mt6762": ["helio", "p22", "a22"],
    "mt6768": ["helio", "g85", "g80"],
    "mt6769": ["helio", "g88", "g85"],
    "mt6785": ["helio", "g90", "g95"],
    "mt6781": ["helio", "g96"],
    "mt6833": ["dimensity", "700", "6020"],
    "mt6853": ["dimensity", "720", "800u"],
    "mt6877": ["dimensity", "900", "920", "1080", "7050"],
    "mt6893": ["dimensity", "1200", "1300"],
    "mt6983": ["dimensity", "9000"],
    "mt6985": ["dimensity", "9200"],
    "mt6989": ["dimensity", "9300"],
    # ── Unisoc ──
    "ums9230": ["unisoc", "t612", "t606", "t616", "t7250"],
    "ums512": ["unisoc", "t610", "t618"],
    "ums9620": ["unisoc", "t760", "t770"],
    # ── Samsung Exynos ──
    "exynos850": ["exynos", "850"],
    "exynos1080": ["exynos", "1080"],
    "exynos1280": ["exynos", "1280"],
    "exynos1380": ["exynos", "1380"],
    "exynos2100": ["exynos", "2100"],
    "exynos2200": ["exynos", "2200"],
    "s5e8825": ["exynos", "1280"],
    "s5e8835": ["exynos", "1380"],
    # ── Google Tensor ──
    "whitechapel": ["tensor", "g1", "gs101"],
    "gs101": ["tensor", "g1", "whitechapel"],
    "gs201": ["tensor", "g2", "cloudripper"],
    "cloudripper": ["tensor", "g2", "gs201"],
    "zuma": ["tensor", "g3"],
}


CHIPSET_MARKETING_MAP = {
    "sm7435": "Snapdragon 7s Gen 2",
    "sm6450": "Snapdragon 6 Gen 1",
    "sm8450": "Snapdragon 8 Gen 1",
    "sm8475": "Snapdragon 8+ Gen 1",
    "sm8550": "Snapdragon 8 Gen 2",
    "sm8650": "Snapdragon 8 Gen 3",
    "sm8750": "Snapdragon 8 Elite",
    "sm8350": "Snapdragon 888",
    "sm7250": "Snapdragon 765G",
    "sm7325": "Snapdragon 778G",
    "sm6375": "Snapdragon 695",
    "sm7450": "Snapdragon 7 Gen 1",
    "sm7475": "Snapdragon 7+ Gen 2",
    "sm6225": "Snapdragon 680",
    "sm7225": "Snapdragon 750G",
    
    "mt6765": "Helio G35",
    "mt6762": "Helio P22",
    "mt6768": "Helio G85",
    "mt6769": "Helio G88",
    "mt6785": "Helio G95",
    "mt6781": "Helio G96",
    "mt6833": "Dimensity 700",
    "mt6853": "Dimensity 720",
    "mt6877": "Dimensity 1080",
    "mt6893": "Dimensity 1200",
    "mt6983": "Dimensity 9000",
    "mt6985": "Dimensity 9200",
    "mt6989": "Dimensity 9300",

    "ums9230": "Unisoc T612",
    "ums512": "Unisoc T618",
    "ums9620": "Unisoc T760",

    "exynos850": "Exynos 850",
    "exynos1080": "Exynos 1080",
    "exynos1280": "Exynos 1280",
    "exynos1380": "Exynos 1380",
    "exynos2100": "Exynos 2100",
    "exynos2200": "Exynos 2200",
    "s5e8825": "Exynos 1280",
    "s5e8835": "Exynos 1380",

    "gs101": "Google Tensor G1",
    "gs201": "Google Tensor G2",
    "zuma": "Google Tensor G3",
}


MODEL_COMMERCIAL_MAP = {
    "rmx5313": "C71",
}

DEVICE_SPECS_OVERRIDE = {
    "realme_c71": {
        "battery": "6300 mAh",
        "chipset": "Unisoc T7250",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "64 GB",
        "overhead": 0.35
    },
    "realme_rmx5313": {
        "battery": "6300 mAh",
        "chipset": "Unisoc T7250",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "64 GB",
        "overhead": 0.35
    }
}


def _featherless_client():
    api_key = os.getenv("FEATHERLESS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set FEATHERLESS_API_KEY in your .env file")
    return OpenAI(base_url="https://api.featherless.ai/v1", api_key=api_key)


def _clean_json(text):
    return text.replace("```json", "").replace("```", "").strip()


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _specs_are_usable(specs):
    if not specs:
        return False
    keys = ("battery", "chipset", "display", "ram", "storage")
    return any(specs.get(k) not in (None, "", "N/A") for k in keys)


def _normalize_specs(specs, source):
    normalized = {**NA_SPECS, **(specs or {})}
    try:
        normalized["overhead"] = float(normalized.get("overhead", 0.25))
    except (TypeError, ValueError):
        normalized["overhead"] = 0.25
    normalized["source"] = source
    return normalized


def _fetch_specs_featherless(brand, model, scanned_ram, scanned_storage, codename):
    client = _featherless_client()
    codename_str = f" (internal codename: {codename})" if codename else ""

    prompt = f"""You are an expert mobile hardware verification engine. Provide ONLY verified official retail specs.

Device: {brand} {model}{codename_str}
Scanned: {scanned_ram or "Unknown"} RAM, {scanned_storage or "Unknown"} storage.

CRITICAL RULES — FOLLOW EXACTLY:
1. Return ONLY specs you are 100% certain are correct for THIS EXACT device.
2. If you are not sure about ANY field, set its value to "N/A". NEVER GUESS.
3. DO NOT copy the example values below. They are schema examples only.
4. Map codenames to commercial labels (e.g. ums9230 -> Unisoc T612, parrot -> Snapdragon 6 Gen 1).
5. Normalize storage to standard retail tiers (64 GB, 128 GB, etc.).
6. Set overhead fraction for storage partition tolerance:
   - Budget phones with heavy partitions: 0.35
   - Premium stock builds: 0.15
   - Default: 0.25
7. Return only valid JSON, no markdown, no explanation.

Schema (EXAMPLE ONLY — do NOT copy these values):
{{
  "battery": "BATTERY_CAPACITY (e.g., 5000 mAh)",
  "chipset": "COMMERCIAL_CHIPSET_NAME (e.g., Snapdragon 8 Gen 2)",
  "display": "RESOLUTION_WIDTHxHEIGHT (e.g., 1080x2400)",
  "ram": "RAM_SIZE (e.g., 8 GB)",
  "storage": "STORAGE_SIZE (e.g., 128 GB)",
  "overhead": 0.25
}}"""

    try:
        response = client.chat.completions.create(
            model=FEATHERLESS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=220,
        )
        parsed = json.loads(_clean_json(response.choices[0].message.content.strip()))
        if _specs_are_usable(parsed):
            return _normalize_specs(parsed, "featherless")
    except Exception as e:
        print(f"Featherless specs error: {e}")
    return None


def _parse_mobileapi_device(device):
    result = {k: "N/A" for k in ("battery", "chipset", "display", "ram", "storage")}
    hw_str = device.get("hardware", "")
    bat = device.get("battery_capacity", "")
    res_str = device.get("screen_resolution", "")
    sto = device.get("storage", "")

    if bat:
        result["battery"] = bat
    if res_str:
        res_match = re.search(r"(\d+x\d+)", res_str)
        if res_match:
            result["display"] = res_match.group(1)
    if sto:
        result["storage"] = sto
    if hw_str:
        ram_match = re.search(r"(\d+(?:/\d+)?GB)\s*RAM", hw_str, re.IGNORECASE)
        if ram_match:
            result["ram"] = ram_match.group(1).split("/")[-1]
        parts = hw_str.split(",")
        if len(parts) >= 2:
            result["chipset"] = parts[-1].strip()
    return result


def _variant_matches(scanned, official):
    if not scanned or not official or official == "N/A":
        return False
    scanned_nums = re.findall(r"\d+(?:\.\d+)?", str(scanned))
    official_nums = re.findall(r"\d+(?:\.\d+)?", str(official))
    if not scanned_nums or not official_nums:
        return False
    s_val = float(scanned_nums[0])
    return any(abs(s_val - float(n)) <= 2 for n in official_nums)


def _fetch_specs_mobileapi(brand, model, scanned_ram, scanned_storage):
    api_key = os.getenv("MOBILE_API_KEY", "").strip()
    if not api_key:
        print("MobileAPI fallback skipped: MOBILE_API_KEY not set")
        return None

    brand_lower = brand.lower().strip()
    queries = []
    for q in (f"{brand} {model}".strip(), model, model.replace(brand_lower, "").strip()):
        if q and q not in queries:
            queries.append(q)

    for query in queries:
        print(f"MobileAPI search: {query}")
        try:
            response = requests.get(
                "https://api.mobileapi.dev/devices/search",
                params={"name": query},
                headers={"Authorization": f"Token {api_key}"},
                timeout=10,
            )
            response.raise_for_status()
            devices = response.json().get("devices", [])
            if not devices:
                continue

            best_specs = None
            for device in devices[:5]:
                parsed = _parse_mobileapi_device(device)
                if scanned_ram and scanned_storage:
                    if _variant_matches(scanned_ram, parsed.get("ram")) and _variant_matches(
                        scanned_storage, parsed.get("storage")
                    ):
                        best_specs = parsed
                        break
                if not best_specs:
                    best_specs = parsed

            if _specs_are_usable(best_specs):
                return _normalize_specs({**best_specs, "overhead": 0.25}, "mobileapi")
        except Exception as e:
            print(f"MobileAPI error: {e}")
    return None


def get_official_specs(brand, model, scanned_ram=None, scanned_storage=None, codename=None, soc_model=None):
    # Check for local specs override first
    override_key = f"{brand}_{model}".lower().replace(" ", "_").strip()
    if override_key in DEVICE_SPECS_OVERRIDE:
        print(f"Using local specs override for: {brand} {model}")
        return _normalize_specs(DEVICE_SPECS_OVERRIDE[override_key], "override")

    cache_key = f"{brand}_{model}".lower()
    cache = load_cache()
    specs = None

    if cache_key in cache:
        cached = _normalize_specs(cache[cache_key], cache[cache_key].get("source", "cache"))
        if _specs_are_usable(cached):
            print(f"Loaded specs from cache: {brand} {model}")
            specs = cached

    # ─── Resolve chipset marketing override helper ───
    resolved_chipset = None
    for val in (soc_model, codename):
        if val:
            val_clean = str(val).lower().strip()
            if val_clean in CHIPSET_MARKETING_MAP:
                resolved_chipset = CHIPSET_MARKETING_MAP[val_clean]
                break

    if not specs:
        # Use either codename or soc_model for AI prompt context
        ai_codename = f"{codename}, {soc_model}" if (codename and soc_model) else (codename or soc_model)
        specs = _fetch_specs_featherless(brand, model, scanned_ram, scanned_storage, ai_codename)
        if not _specs_are_usable(specs):
            specs = _fetch_specs_mobileapi(brand, model, scanned_ram, scanned_storage)

        if _specs_are_usable(specs):
            if resolved_chipset:
                specs["chipset"] = resolved_chipset
            cache[cache_key] = {k: specs[k] for k in specs if k != "source"}
            save_cache(cache)
        else:
            specs = dict(NA_SPECS)
    else:
        if resolved_chipset:
            specs["chipset"] = resolved_chipset

    return specs


def _default_comparison(message="Could not verify"):
    return {"status": "unknown", "flag": "warn", "message": message}


def _compare_battery(level, health):
    """Battery health from ADB only — mAh cannot be verified, so never flag as suspicious for that."""
    bad = {"Dead", "Failure", "Overheat", "Over Voltage"}
    if health in bad:
        return {
            "status": "suspicious",
            "flag": "danger",
            "message": f"Battery health reports {health}",
        }
    try:
        lvl = int(level) if level and level != "N/A" else None
    except (TypeError, ValueError):
        lvl = None

    if health == "Good":
        pct = f"{lvl}%" if lvl is not None else "N/A"
        return {
            "status": "genuine",
            "flag": "ok",
            "message": f"Battery healthy at {pct}",
        }
    return {
        "status": "genuine",
        "flag": "ok",
        "message": f"Battery at {level}% — {health}",
    }


def _compare_local(scanned, official, overhead=0.25):
    if not official or official == "N/A" or scanned == "N/A":
        return _default_comparison("No validation data")

    s_clean = str(scanned).lower().strip()
    o_clean = str(official).lower().strip()

    if s_clean in o_clean or o_clean in s_clean:
        return {"status": "genuine", "flag": "ok", "message": "Match found"}

    for key, tokens in HARDWARE_SYNONYMS.items():
        if key in s_clean or key in o_clean:
            if any(t in s_clean for t in tokens) or any(t in o_clean for t in tokens):
                return {
                    "status": "genuine",
                    "flag": "ok",
                    "message": f"Match verified ({official})",
                }

    s_nums = re.findall(r"\d+(?:\.\d+)?", s_clean)
    o_nums = re.findall(r"\d+(?:\.\d+)?", o_clean)
    if s_nums and o_nums:
        s_val = float(s_nums[0])
        for o_val in (float(n) for n in o_nums):
            if s_val >= o_val * (1.0 - overhead) and s_val <= o_val * 1.1:
                return {"status": "genuine", "flag": "ok", "message": "Match within tolerance"}

    return {
        "status": "suspicious",
        "flag": "danger",
        "message": f"Mismatch: {scanned} vs {official}",
    }


def _verify_chipset_with_ai(scanned, official):
    """AI fallback: ask Featherless if a scanned codename matches an official chipset."""
    try:
        client = _featherless_client()
        prompt = f"""You are a mobile hardware database expert.
Determine if the scanned chipset/board platform '{scanned}' corresponds to the official chipset '{official}'.

Android devices report internal codenames via ADB (e.g. 'parrot' for Snapdragon 6 Gen 1,
'bengal' for Snapdragon 680, 'lahaina' for Snapdragon 888, 'mt6765' for Helio G35/P35,
'pineapple' for Snapdragon 8 Gen 3, 'taro' for Snapdragon 8 Gen 1,
'ums9230' for Unisoc T612, 'zuma' for Tensor G3).

These codenames often differ completely from the marketing name.
Return ONLY a raw JSON object (no markdown, no explanation):
{{{{
  "match": true,
  "confidence": "high",
  "explanation": "Brief reason."
}}}}"""  # noqa: E501

        response = client.chat.completions.create(
            model=FEATHERLESS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=120,
        )
        result = json.loads(_clean_json(response.choices[0].message.content.strip()))
        return result
    except Exception as e:
        print(f"AI chipset verification error: {e}")
        return None


def _compare_chipset(scanned, official):
    """Compare chipset with local matching first, then AI fallback for unknown codenames."""
    if not official or official == "N/A" or not scanned or scanned == "N/A":
        return _default_comparison("No validation data")

    s_clean = str(scanned).lower().strip()
    o_clean = str(official).lower().strip()

    # Direct substring match
    if s_clean in o_clean or o_clean in s_clean:
        return {"status": "genuine", "flag": "ok", "message": "Match found"}

    # Local synonym table lookup
    for key, tokens in HARDWARE_SYNONYMS.items():
        if key in s_clean or key in o_clean:
            if any(t in s_clean for t in tokens) or any(t in o_clean for t in tokens):
                return {
                    "status": "genuine",
                    "flag": "ok",
                    "message": f"Match verified ({official})",
                }

    # AI fallback for codenames not in our local table
    print(f"Chipset not in local table, asking AI: '{scanned}' vs '{official}'")
    ai_result = _verify_chipset_with_ai(scanned, official)
    if ai_result and ai_result.get("match") is True:
        confidence = ai_result.get("confidence", "unknown")
        explanation = ai_result.get("explanation", "AI verified")
        if confidence in ("high", "medium"):
            return {
                "status": "genuine",
                "flag": "ok",
                "message": f"AI verified: {explanation}",
            }
        else:
            return {
                "status": "unknown",
                "flag": "warn",
                "message": f"Low confidence: {explanation}",
            }
    elif ai_result and ai_result.get("match") is False:
        return {
            "status": "suspicious",
            "flag": "danger",
            "message": f"Mismatch: {scanned} vs {official}",
        }

    # If AI also fails, warn instead of flagging as suspicious
    return _default_comparison(f"Could not verify: {scanned} vs {official}")


def compare_device(scanned, official, device_info=None):
    """Fast local comparison. Featherless is used for spec lookup only, except chipset AI fallback."""
    if not _specs_are_usable(official):
        return {
            "display": _default_comparison("Official specs unavailable"),
            "ram": _default_comparison("Official specs unavailable"),
            "storage": _default_comparison("Official specs unavailable"),
            "chipset": _default_comparison("Official specs unavailable"),
            "battery": _compare_battery(scanned.get("battery_level"), scanned.get("battery_health")),
        }

    overhead = float(official.get("overhead", 0.25))
    return {
        "display": _compare_local(scanned.get("display"), official.get("display"), 0.1),
        "ram": _compare_local(scanned.get("ram"), official.get("ram"), 0.2),
        "storage": _compare_local(scanned.get("storage"), official.get("storage"), overhead),
        "chipset": _compare_chipset(scanned.get("chipset"), official.get("chipset")),
        "battery": _compare_battery(scanned.get("battery_level"), scanned.get("battery_health")),
    }
