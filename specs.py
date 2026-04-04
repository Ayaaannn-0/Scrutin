import os
import re
from urllib.parse import quote

from dotenv import load_dotenv
import requests

load_dotenv()


RAPIDAPI_HOST = "mobile-phone-specs-database.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"


def _flatten_strings(value):
    """Collect all scalar values from nested response objects."""
    out = []
    if isinstance(value, dict):
        for v in value.values():
            out.extend(_flatten_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(_flatten_strings(v))
    elif value is not None:
        out.append(str(value))
    return out


def _find_field(data, keys):
    """Find first value where key contains any target token."""
    if isinstance(data, dict):
        for k, v in data.items():
            lk = str(k).lower()
            if any(token in lk for token in keys):
                vals = _flatten_strings(v)
                if vals:
                    return " | ".join(vals)
        for v in data.values():
            found = _find_field(v, keys)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_field(item, keys)
            if found:
                return found
    return None


def _parse_first_gb(text):
    if not text:
        return None
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*gb", str(text), re.IGNORECASE)
    if not nums:
        return None
    try:
        return float(nums[0])
    except ValueError:
        return None


def _extract_unique_gb_values(text):
    vals = re.findall(
        r"\b(2|3|4|6|8|12|16|24|32|64|128|256|512|1024)\s*gb\b",
        text,
        re.IGNORECASE,
    )
    ordered = []
    for v in vals:
        iv = int(v)
        if iv not in ordered:
            ordered.append(iv)
    return ordered


def _extract_battery_capacity(text):
    m = re.search(r"\b(\d{3,5})\s*mAh\b", text, re.IGNORECASE)
    if m:
        return f"{m.group(1)} mAh"
    return "N/A"


def _extract_resolution(text):
    m = re.search(r"(\d{3,4})\s*[xX]\s*(\d{3,4})", text)
    if m:
        return f"{m.group(1)}x{m.group(2)}"
    return "N/A"


def _choose_nearest_option(scanned_value, options):
    if scanned_value is None or not options:
        return None
    return min(options, key=lambda x: abs(float(x) - float(scanned_value)))


def _extract_official_fields(payload, scanned_ram=None, scanned_storage=None):
    text_blob = " ".join(_flatten_strings(payload))

    battery_raw = _find_field(payload, ["battery"]) or ""
    display_raw = (
        _find_field(payload, ["resolution"])
        or _find_field(payload, ["display"])
        or ""
    )
    chipset_raw = _find_field(payload, ["chipset", "soc", "processor"]) or "N/A"

    ram_options = [v for v in _extract_unique_gb_values(text_blob) if v <= 24]
    storage_options = [v for v in _extract_unique_gb_values(text_blob) if v >= 32]

    scanned_ram_gb = _parse_first_gb(scanned_ram)
    scanned_storage_gb = _parse_first_gb(scanned_storage)

    selected_ram = _choose_nearest_option(scanned_ram_gb, ram_options)
    selected_storage = _choose_nearest_option(scanned_storage_gb, storage_options)

    confidence = "high"
    reasons = []
    if selected_ram is None:
        confidence = "low"
        reasons.append("ram option unavailable")
    if selected_storage is None:
        confidence = "low"
        reasons.append("storage option unavailable")
    if selected_ram is not None and scanned_ram_gb is not None:
        if abs(selected_ram - scanned_ram_gb) > 2.0:
            confidence = "low"
            reasons.append("ram far from scanned value")
    if selected_storage is not None and scanned_storage_gb is not None:
        if abs(selected_storage - scanned_storage_gb) > 64:
            confidence = "low"
            reasons.append("storage far from scanned value")

    return {
        "battery": _extract_battery_capacity(battery_raw or text_blob),
        "chipset": str(chipset_raw).split(" | ")[0] if chipset_raw else "N/A",
        "display": _extract_resolution(display_raw or text_blob),
        "ram": f"{selected_ram} GB" if selected_ram is not None else "N/A",
        "storage": f"{selected_storage} GB" if selected_storage is not None else "N/A",
        "variant_confidence": confidence,
        "variant_reason": ", ".join(reasons) if reasons else "ram+storage matched",
        "ram_options_gb": ram_options,
        "storage_options_gb": storage_options,
    }


def get_official_specs(brand, model, scanned_ram=None, scanned_storage=None):
    api_key = os.getenv("MOBILE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set MOBILE_API_KEY in .env")

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    brand_enc = quote(str(brand).strip(), safe="")
    model_enc = quote(str(model).strip(), safe="")
    model_compact_enc = quote(str(model).replace(" ", "").strip(), safe="")
    paths = [
        f"/gsm/get-specifications-by-brandname-modelname/{brand_enc}/{model_enc}",
        f"/gsm/get-specifications-by-brandname-modelname/{brand_enc}/{model_compact_enc}",
    ]

    last_error = None
    for path in paths:
        url = f"{RAPIDAPI_BASE_URL}{path}"
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                last_error = f"{resp.status_code}: {resp.text[:120]}"
                continue
            payload = resp.json()
            official = _extract_official_fields(
                payload,
                scanned_ram=scanned_ram,
                scanned_storage=scanned_storage,
            )
            if any(official.get(k) != "N/A" for k in ("chipset", "display", "ram", "storage")):
                return official
        except Exception as exc:
            last_error = str(exc)

    raise RuntimeError(f"RapidAPI lookup failed: {last_error or 'no usable response'}")