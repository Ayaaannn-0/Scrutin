from adb_utils import (
    clean_model_name,
    list_adb_devices,
    parse_battery,
    parse_ram,
    parse_resolution,
    parse_storage,
    run_adb,
)


def main():
    devices = list_adb_devices()
    if not devices:
        print("No ADB device found. Connect a phone with USB debugging enabled.")
        return
    if len(devices) > 1:
        print("Multiple devices connected. Connect only one device.")
        return

    serial = devices[0]
    brand = run_adb("getprop ro.product.brand", serial)
    model = run_adb("getprop ro.product.model", serial)
    android = run_adb("getprop ro.build.version.release", serial)
    chipset = run_adb("getprop ro.board.platform", serial)
    resolution = parse_resolution(run_adb("wm size", serial))
    battery = parse_battery(run_adb("dumpsys battery", serial))
    storage = parse_storage(run_adb("df /data", serial))
    ram = parse_ram(run_adb("cat /proc/meminfo", serial))

    print()
    print("╔══════════════════════════════╗")
    print("║        SCRUTIN  SCAN         ║")
    print("╚══════════════════════════════╝")
    print()
    print("─── Device ───────────────────")
    print(f"  Brand      : {brand.capitalize()}")
    print(f"  Model      : {model}")
    print(f"  Clean name : {clean_model_name(brand, model)}")
    print(f"  Android    : {android}")
    print(f"  Chipset    : {chipset}")
    print()
    print("─── Display ──────────────────")
    print(f"  Resolution : {resolution}")
    print()
    print("─── Battery ──────────────────")
    print(f"  Level      : {battery.get('level', 'N/A')}%")
    print(f"  Health     : {battery.get('health', 'N/A')}")
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


if __name__ == "__main__":
    main()
