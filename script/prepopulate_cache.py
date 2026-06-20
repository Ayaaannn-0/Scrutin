import json
import os

CACHE_FILE = r"c:\Users\ayaan\scrutin 0.2\specs_cache.json"

db = {
    # Redmi Series
    "redmi_2406ern9ci": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 6100+",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.35
    },
    "redmi_23124rn87i": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 6100+",
        "display": "720x1600",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.35
    },
    "redmi_23076rn4bi": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 4 Gen 2",
        "display": "1080x2460",
        "ram": "4 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "redmi_23090ra98g": {
        "battery": "5100 mAh",
        "chipset": "Snapdragon 7s Gen 2",
        "display": "1220x2712",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "redmi_note_13_pro": {
        "battery": "5100 mAh",
        "chipset": "Snapdragon 7s Gen 2",
        "display": "1220x2712",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "redmi_note_12_pro": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 1080",
        "display": "1080x2400",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    # Vivo Series
    "vivo_v2247": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 680",
        "display": "1080x2408",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "vivo_v2225": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 6020",
        "display": "1080x2408",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "60 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "vivo_v2207": {
        "battery": "5000 mAh",
        "chipset": "Helio P35",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "64 GB",
        "refresh_rate": "60 Hz",
        "storage_type": "eMMC 5.1",
        "overhead": 0.35
    },
    "vivo_v2025": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 460",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "64 GB",
        "refresh_rate": "60 Hz",
        "storage_type": "eMMC 5.1",
        "overhead": 0.35
    },
    "vivo_v2303": {
        "battery": "4600 mAh",
        "chipset": "Snapdragon 778G",
        "display": "1260x2800",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    # Samsung Series
    "samsung_sm-a146b": {
        "battery": "5000 mAh",
        "chipset": "Exynos 1330",
        "display": "1080x2408",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "samsung_sm-a346b": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 1080",
        "display": "1080x2340",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "samsung_sm-a546b": {
        "battery": "5000 mAh",
        "chipset": "Exynos 1380",
        "display": "1080x2340",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "samsung_sm-m346b": {
        "battery": "6000 mAh",
        "chipset": "Exynos 1280",
        "display": "1080x2340",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.35
    },
    "samsung_sm-m146b": {
        "battery": "6000 mAh",
        "chipset": "Exynos 1330",
        "display": "1080x2408",
        "ram": "4 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.35
    },
    "samsung_sm-s928b": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 8 Gen 3",
        "display": "1440x3120",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 4.0",
        "overhead": 0.15
    },
    "samsung_sm-s928u": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 8 Gen 3",
        "display": "1440x3120",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 4.0",
        "overhead": 0.15
    },
    "samsung_sm-s918b": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 8 Gen 2",
        "display": "1440x3088",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 4.0",
        "overhead": 0.15
    },
    "samsung_sm-s918u": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 8 Gen 2",
        "display": "1440x3088",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 4.0",
        "overhead": 0.15
    },
    # Realme Series
    "realme_rmx3762": {
        "battery": "5000 mAh",
        "chipset": "Unisoc T612",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "64 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "eMMC 5.1",
        "overhead": 0.35
    },
    "realme_rmx3710": {
        "battery": "5000 mAh",
        "chipset": "Helio G88",
        "display": "1080x2400",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "eMMC 5.1",
        "overhead": 0.35
    },
    "realme_rmx3771": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 7050",
        "display": "1080x2412",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "realme_rmx3842": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 6 Gen 1",
        "display": "1080x2412",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    # Motorola Series
    "motorola_moto_g54": {
        "battery": "6000 mAh",
        "chipset": "Dimensity 7020",
        "display": "1080x2400",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "motorola_moto_g34": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 695",
        "display": "720x1600",
        "ram": "4 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.35
    },
    "motorola_moto_g84": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 695",
        "display": "1080x2400",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    # OnePlus Series
    "oneplus_cph2467": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 695",
        "display": "1080x2400",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "oneplus_cph2381": {
        "battery": "5000 mAh",
        "chipset": "Snapdragon 695",
        "display": "1080x2412",
        "ram": "6 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 2.2",
        "overhead": 0.25
    },
    "oneplus_cph2493": {
        "battery": "5000 mAh",
        "chipset": "Dimensity 9000",
        "display": "1240x2772",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 3.1",
        "overhead": 0.25
    },
    "oneplus_cph2573": {
        "battery": "5400 mAh",
        "chipset": "Snapdragon 8 Gen 3",
        "display": "1440x3168",
        "ram": "12 GB",
        "storage": "256 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 4.0",
        "overhead": 0.15
    },
    # Google Series
    "google_gc3ve": {
        "battery": "5050 mAh",
        "chipset": "Tensor G3",
        "display": "1344x2992",
        "ram": "12 GB",
        "storage": "128 GB",
        "refresh_rate": "120 Hz",
        "storage_type": "UFS 3.1",
        "overhead": 0.15
    },
    "google_gvu6c": {
        "battery": "4355 mAh",
        "chipset": "Tensor G2",
        "display": "1080x2400",
        "ram": "8 GB",
        "storage": "128 GB",
        "refresh_rate": "90 Hz",
        "storage_type": "UFS 3.1",
        "overhead": 0.15
    }
}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            current = json.load(f)
    except Exception:
        current = {}
else:
    current = {}

current.update(db)

with open(CACHE_FILE, "w", encoding="utf-8") as f:
    json.dump(current, f, indent=2)

print("Prepopulated database successfully!")
