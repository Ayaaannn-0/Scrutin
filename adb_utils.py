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
    }
    if not raw:
        return data

    level_match = re.search(r"\blevel:\s*(\d+)", raw)
    health_match = re.search(r"\bhealth:\s*(\d+)", raw)
    temp_match = re.search(r"\btemperature:\s*(\d+)", raw)
    volt_match = re.search(r"\bvoltage:\s*(\d+)", raw)
    tech_match = re.search(r"\btechnology:\s*([^\s]+)", raw)

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
            if len(sensors) >= 12:
                break
    return sensors
