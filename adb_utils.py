import re
import subprocess

ADB_TIMEOUT = 4


def list_adb_devices():
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=ADB_TIMEOUT,
        )
        devices = []
        for line in result.stdout.strip().splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices
    except Exception as e:
        print(f"ADB devices error: {e}")
        return []


def run_adb(command, serial=None):
    try:
        cmd = ["adb"]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(["shell", command])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=ADB_TIMEOUT,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception as e:
        print(f"ADB error ({command}): {e}")
        return ""


def clean_model_name(brand, model):
    original = model.strip()
    brand_clean = brand.strip()
    brand_lower = brand_clean.lower()
    model_lower = original.lower()
    
    if brand_lower and model_lower.startswith(brand_lower):
        cleaned = original[len(brand_lower):].strip()
    else:
        cleaned = original
        
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
        
    return cleaned or original


def parse_battery(raw):
    data = {
        "level": "N/A",
        "health": "Unknown",
        "temperature": "N/A",
        "voltage": "N/A",
        "technology": "Li-ion",
        "cycle_count": "N/A",
    }
    if not raw:
        return data

    level_match = re.search(r"^\s*level:\s*(\d+)", raw, re.MULTILINE)
    health_match = re.search(r"^\s*health:\s*(\d+)", raw, re.MULTILINE)
    temp_match = re.search(r"^\s*temperature:\s*(\d+)", raw, re.MULTILINE)
    volt_match = re.search(r"^\s*voltage:\s*(\d+)", raw, re.MULTILINE)
    tech_match = re.search(r"^\s*technology:\s*([^\s]+)", raw, re.MULTILINE)
    cycle_match = re.search(r"^\s*(?:cycle count|cycle_count|cycles|Cycle count):\s*(\d+)", raw, re.MULTILINE | re.IGNORECASE)

    if level_match:
        data["level"] = level_match.group(1)
    if temp_match:
        data["temperature"] = f"{float(temp_match.group(1)) / 10}°C"
    if volt_match:
        v_val = int(volt_match.group(1))
        if v_val > 10000:
            v_val = round(v_val / 1000)
        data["voltage"] = f"{v_val} mV"
    if tech_match:
        data["technology"] = tech_match.group(1)
    if cycle_match:
        data["cycle_count"] = cycle_match.group(1)

    health_map = {
        "1": "Unknown",
        "2": "Good",
        "3": "Overheat",
        "4": "Dead",
        "5": "Over Voltage",
        "6": "Failure",
        "7": "Cold",
    }
    if health_match:
        data["health"] = health_map.get(health_match.group(1), "Unknown")
    return data


def parse_storage(raw):
    fallback = {"total": "N/A", "used": "N/A", "free": "N/A"}
    if not raw:
        return fallback
    try:
        lines = raw.splitlines()
        if len(lines) < 2:
            return fallback
        parts = lines[1].split()
        if len(parts) < 4:
            return fallback
        return {
            "total": f"{round(int(parts[1]) / 1024 / 1024, 1)} GB",
            "used": f"{round(int(parts[2]) / 1024 / 1024, 1)} GB",
            "free": f"{round(int(parts[3]) / 1024 / 1024, 1)} GB",
        }
    except (ValueError, IndexError):
        return fallback


def parse_ram(raw):
    data = {"total": "N/A", "available": "N/A"}
    if not raw:
        return data
    try:
        for line in raw.splitlines():
            if "MemTotal:" in line:
                data["total"] = f"{round(int(line.split()[1]) / 1024 / 1024, 1)} GB"
            if "MemAvailable:" in line:
                data["available"] = f"{round(int(line.split()[1]) / 1024 / 1024, 1)} GB"
    except (ValueError, IndexError):
        pass
    return data


def parse_resolution(raw):
    if not raw:
        return "N/A"
    match = re.search(r"Physical size:\s*(\d+x\d+)", raw)
    if match:
        return match.group(1)
    match = re.search(r"(\d+x\d+)", raw)
    return match.group(1) if match else "N/A"


def parse_sensors(raw_dumpsys):
    sensors = []
    if not raw_dumpsys:
        return sensors
    
    for line in raw_dumpsys.splitlines():
        line = line.strip()
        if not line or not line.startswith("0x") or ") " not in line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            # Parse sensor name
            name_part = parts[0]
            if ")" in name_part:
                name = name_part.split(")")[-1].strip()
            else:
                name = name_part
                
            vendor = parts[1]
            
            # Parse sensor type
            type_part = parts[3]
            sensor_type = "Unknown"
            if "type:" in type_part:
                t_val = type_part.split("type:")[-1].strip()
                if "(" in t_val:
                    sensor_type = t_val.split("(")[0].strip()
                else:
                    sensor_type = t_val
            
            if sensor_type.startswith("android.sensor."):
                sensor_type = sensor_type.replace("android.sensor.", "").replace("_", " ").capitalize()
            
            sensors.append({
                "name": name,
                "vendor": vendor,
                "type": sensor_type
            })
            if len(sensors) >= 150:
                break
    return sensors


def parse_refresh_rate(raw_dumpsys_display, raw_settings_peak=None):
    if raw_settings_peak:
        try:
            val = float(raw_settings_peak.strip())
            if val > 0:
                return f"{round(val)} Hz"
        except ValueError:
            pass

    if not raw_dumpsys_display:
        return "60 Hz"

    # Pattern 1: e.g. "fps=120"
    match = re.search(r"\bfps=(\d+)", raw_dumpsys_display)
    if match:
        return f"{match.group(1)} Hz"

    # Pattern 2: e.g. "refreshRate=120.0"
    match = re.search(r"\brefreshRate=(\d+(?:\.\d+)?)", raw_dumpsys_display)
    if match:
        return f"{round(float(match.group(1)))} Hz"

    # Pattern 3: e.g. "mPhys=1080x2400@120.00"
    match = re.search(r"@(\d+(?:\.\d+)?)", raw_dumpsys_display)
    if match:
        return f"{round(float(match.group(1)))} Hz"

    return "60 Hz"


def run_storage_benchmark(serial=None):
    import time
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", "dd if=/dev/zero of=/data/local/tmp/speedtest bs=102400 count=200"])
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        duration = time.time() - start_time
        
        cleanup_cmd = ["adb"]
        if serial:
            cleanup_cmd.extend(["-s", serial])
        cleanup_cmd.extend(["shell", "rm -f /data/local/tmp/speedtest"])
        subprocess.run(cleanup_cmd, capture_output=True)
        
        speed = round(20.48 / duration, 1) if duration > 0 else 0
        raw_stats = result.stderr.strip() or result.stdout.strip()
        if not raw_stats:
            raw_stats = f"20480000 bytes transferred in {round(duration, 3)}s ({speed} MB/s)"
        
        return {
            "speed_mbs": speed,
            "raw_output": raw_stats
        }
    except Exception as e:
        return {
            "speed_mbs": 0,
            "raw_output": f"Benchmark failed: {str(e)}"
        }
