import os
import json

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, Response
from flask_cors import CORS
from openai import OpenAI

from adb_utils import (
    clean_model_name,
    list_adb_devices,
    parse_battery,
    parse_ram,
    parse_resolution,
    parse_storage,
    run_adb,
    parse_sensors,
    parse_refresh_rate,
    run_storage_benchmark,
)
from specs import compare_device, get_official_specs, MODEL_COMMERCIAL_MAP

load_dotenv()

app = Flask(__name__)
CORS(app)

FEATHERLESS_MODEL = "Qwen/Qwen2.5-72B-Instruct"


def _compute_trust_score(comparisons, verified):
    if not verified:
        return None
    score = 10.0
    for key, comp in comparisons.items():
        if key == "battery":
            if comp["flag"] == "danger":
                score -= 1
            continue
        if comp["flag"] == "danger":
            score -= 2
        elif comp["flag"] == "warn":
            score -= 0.5
    return max(0, round(score))


@app.route("/")
def index():
    return render_template("scrutin2.html")


@app.route("/scan")
def scan():
    try:
        devices = list_adb_devices()
        if not devices:
            return jsonify({"error": "No USB device detected. Enable USB debugging and connect your phone."}), 400
        if len(devices) > 1:
            return jsonify({"error": "Multiple devices connected. Disconnect extras or specify one device."}), 400

        serial = devices[0]
        brand = run_adb("getprop ro.product.brand", serial).capitalize()
        raw_model = run_adb("getprop ro.product.model", serial)

        if not brand or not raw_model:
            return jsonify({"error": "Could not read device properties over ADB."}), 400

        model = clean_model_name(brand, raw_model)
        model_key = model.lower().strip()
        if model_key in MODEL_COMMERCIAL_MAP:
            model = MODEL_COMMERCIAL_MAP[model_key]
        android = run_adb("getprop ro.build.version.release", serial)
        chipset_raw = run_adb("getprop ro.board.platform", serial)
        soc_model = run_adb("getprop ro.soc.model", serial)

        resolution = parse_resolution(run_adb("wm size", serial))
        battery = parse_battery(run_adb("dumpsys battery", serial))
        storage = parse_storage(run_adb("df /data", serial))
        ram = parse_ram(run_adb("cat /proc/meminfo", serial))
        sensors_raw = run_adb("dumpsys sensorservice", serial)
        sensors = parse_sensors(sensors_raw)
        try:
            official = get_official_specs(
                brand=brand,
                model=model,
                scanned_ram=ram.get("total"),
                scanned_storage=storage.get("total"),
                codename=chipset_raw,
                soc_model=soc_model,
            )
        except Exception as e:
            print(f"Spec lookup error: {e}")
            official = {
                "battery": "N/A",
                "chipset": "N/A",
                "display": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "overhead": 0.25,
                "source": "none",
            }

        verified = official.get("source") not in (None, "none") and any(
            official.get(k) != "N/A" for k in ("battery", "chipset", "display", "ram", "storage")
        )

        scanned_for_compare = {
            "display": resolution,
            "ram": ram.get("total"),
            "storage": storage.get("total"),
            "chipset": chipset_raw or soc_model,
            "battery_level": battery.get("level"),
            "battery_health": battery.get("health"),
        }

        device_info = {"brand": brand, "model": model, "codename": chipset_raw or soc_model}
        comparisons = compare_device(scanned_for_compare, official, device_info)
        trust_score = _compute_trust_score(comparisons, verified)

        display_chipset = chipset_raw
        if official.get("chipset") not in (None, "", "N/A"):
            display_chipset = official.get("chipset")

        return jsonify(
            {
                "device": {
                    "brand": brand,
                    "model": model,
                    "android": android,
                    "chipset": display_chipset,
                    "codename": chipset_raw,
                    "soc_model": soc_model or "N/A",
                },
                "battery": battery,
                "display": {"resolution": resolution},
                "ram": ram,
                "storage": storage,
                "sensors": sensors,
                "official": official,
                "comparisons": comparisons,
                "trust_score": trust_score,
                "verification_status": "verified" if verified else "unverified",
            }
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(tb)
        return jsonify({"error": str(e), "traceback": tb}), 500


@app.route("/scan_stream")
def scan_stream():
    def generate():
        import json
        import time
        import traceback

        def sse(t, val):
            return f"data: {json.dumps({'type': t, **val})}\n\n"

        try:
            yield sse("sys", {"text": "Initializing Scrutin forensic console..."})
            time.sleep(0.05)
            
            yield sse("sys", {"text": "Scanning for connected USB debugging devices..."})
            yield sse("cmd", {"text": "adb devices"})
            devices = list_adb_devices()

            if not devices:
                yield sse("err", {"text": "No USB device detected. Please enable USB debugging and reconnect."})
                return
            if len(devices) > 1:
                yield sse("err", {"text": "Multiple devices detected. Please connect only one device."})
                return

            serial = devices[0]
            yield sse("success", {"text": f"Device detected: serial={serial}"})
            time.sleep(0.05)

            # 1. Battery Step
            yield sse("step", {"name": "bat", "status": "active", "p": "20%"})
            yield sse("sys", {"text": "Interrogating battery controller subsystem..."})
            yield sse("cmd", {"text": f"adb -s {serial} shell dumpsys battery"})
            battery_raw = run_adb("dumpsys battery", serial)
            battery = parse_battery(battery_raw)
            
            if battery_raw:
                lines = [l.strip() for l in battery_raw.splitlines() if l.strip()][:4]
                for line in lines:
                    yield sse("stdout", {"text": f"  {line}"})
            
            yield sse("success", {"text": f"Battery parsed: Level {battery.get('level') or 'N/A'}%, Health {battery.get('health') or 'Unknown'}"})
            time.sleep(0.05)

            # 2. Storage Step
            yield sse("step", {"name": "bat", "status": "done", "p": "20%"})
            yield sse("step", {"name": "sto", "status": "active", "p": "40%"})
            yield sse("sys", {"text": "Analyzing system partition blocks..."})
            yield sse("cmd", {"text": f"adb -s {serial} shell df /data"})
            storage_raw = run_adb("df /data", serial)
            storage = parse_storage(storage_raw)
            if storage_raw:
                lines = [l.strip() for l in storage_raw.splitlines() if l.strip()][:2]
                for line in lines:
                    yield sse("stdout", {"text": f"  {line}"})
            yield sse("success", {"text": f"Storage parsed: Total {storage.get('total') or 'N/A'}, Free {storage.get('free') or 'N/A'}"})
            time.sleep(0.05)

            # Storage Speed Benchmark
            yield sse("sys", {"text": "Running active storage I/O speed benchmark..."})
            yield sse("cmd", {"text": f"adb -s {serial} shell dd if=/dev/zero of=/data/local/tmp/speedtest bs=102400 count=200"})
            bench = run_storage_benchmark(serial)
            storage_speed = bench["speed_mbs"]
            if bench["raw_output"]:
                for line in bench["raw_output"].splitlines():
                    if line.strip():
                        yield sse("stdout", {"text": f"  {line.strip()}"})
            yield sse("success", {"text": f"Storage speed test completed. Write speed: {storage_speed} MB/s"})
            time.sleep(0.05)

            # 3. CPU / Identity Step
            yield sse("step", {"name": "sto", "status": "done", "p": "40%"})
            yield sse("step", {"name": "cpu", "status": "active", "p": "60%"})
            yield sse("sys", {"text": "Retrieving hardware build properties..."})
            
            yield sse("cmd", {"text": f"adb -s {serial} shell getprop ro.product.brand"})
            brand = run_adb("getprop ro.product.brand", serial).capitalize()
            yield sse("stdout", {"text": f"  ro.product.brand: {brand}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell getprop ro.product.model"})
            raw_model = run_adb("getprop ro.product.model", serial)
            yield sse("stdout", {"text": f"  ro.product.model: {raw_model}"})

            if not brand or not raw_model:
                yield sse("err", {"text": "Could not read device properties over ADB."})
                return

            model = clean_model_name(brand, raw_model)
            model_key = model.lower().strip()
            if model_key in MODEL_COMMERCIAL_MAP:
                model = MODEL_COMMERCIAL_MAP[model_key]

            yield sse("cmd", {"text": f"adb -s {serial} shell getprop ro.build.version.release"})
            android = run_adb("getprop ro.build.version.release", serial)
            yield sse("stdout", {"text": f"  ro.build.version.release: {android}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell getprop ro.board.platform"})
            chipset_raw = run_adb("getprop ro.board.platform", serial)
            yield sse("stdout", {"text": f"  ro.board.platform: {chipset_raw}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell getprop ro.soc.model"})
            soc_model = run_adb("getprop ro.soc.model", serial)
            yield sse("stdout", {"text": f"  ro.soc.model: {soc_model}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell cat /proc/meminfo"})
            ram_raw = run_adb("cat /proc/meminfo", serial)
            ram = parse_ram(ram_raw)
            if ram_raw:
                lines = [l.strip() for l in ram_raw.splitlines() if "MemTotal" in l or "MemAvailable" in l]
                for line in lines:
                    yield sse("stdout", {"text": f"  {line}"})
            yield sse("success", {"text": f"RAM parsed: Total {ram.get('total') or 'N/A'}"})
            time.sleep(0.05)

            # 4. Display & Sensors Step
            yield sse("step", {"name": "cpu", "status": "done", "p": "60%"})
            yield sse("step", {"name": "dsp", "status": "active", "p": "80%"})
            
            yield sse("sys", {"text": "Auditing display panel geometry & refresh rates..."})
            yield sse("cmd", {"text": f"adb -s {serial} shell wm size"})
            size_raw = run_adb("wm size", serial)
            resolution = parse_resolution(size_raw)
            if size_raw:
                yield sse("stdout", {"text": f"  {size_raw}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell settings get system peak_refresh_rate"})
            settings_hz_raw = run_adb("settings get system peak_refresh_rate", serial)
            if settings_hz_raw:
                yield sse("stdout", {"text": f"  peak_refresh_rate: {settings_hz_raw}"})

            yield sse("cmd", {"text": f"adb -s {serial} shell dumpsys display"})
            display_raw = run_adb("dumpsys display", serial)
            refresh_rate = parse_refresh_rate(display_raw, settings_hz_raw)
            yield sse("stdout", {"text": f"  Detected refresh rate: {refresh_rate}"})

            yield sse("sys", {"text": "Mapping active hardware sensors..."})
            yield sse("cmd", {"text": f"adb -s {serial} shell dumpsys sensorservice"})
            sensors_raw = run_adb("dumpsys sensorservice", serial)
            sensors = parse_sensors(sensors_raw)
            yield sse("success", {"text": f"Display: {resolution} ({refresh_rate}). Sensors: {len(sensors)} active."})
            time.sleep(0.05)

            # 5. AI Specs Correlation
            yield sse("step", {"name": "dsp", "status": "done", "p": "80%"})
            yield sse("step", {"name": "ai", "status": "active", "p": "90%"})
            yield sse("sys", {"text": f"Accessing device database for {brand} {model}..."})
            
            official = {
                "battery": "N/A",
                "chipset": "N/A",
                "display": "N/A",
                "ram": "N/A",
                "storage": "N/A",
                "overhead": 0.25,
                "source": "none",
            }
            try:
                official = get_official_specs(
                    brand=brand,
                    model=model,
                    scanned_ram=ram.get("total"),
                    scanned_storage=storage.get("total"),
                    codename=chipset_raw,
                    soc_model=soc_model,
                )
                yield sse("success", {"text": f"Official specs fetched (Source: {official.get('source', 'none')})"})
            except Exception as e:
                yield sse("err", {"text": f"Specs lookup failure: {str(e)}. Using fallback profile."})

            # 6. Final Comparisons & Matrix
            yield sse("step", {"name": "ai", "status": "done", "p": "90%"})
            yield sse("step", {"name": "cmp", "status": "active", "p": "100%"})
            yield sse("sys", {"text": "Generating forensic comparison matrix..."})

            verified = official.get("source") not in (None, "none") and any(
                official.get(k) != "N/A" for k in ("battery", "chipset", "display", "ram", "storage")
            )

            scanned_for_compare = {
                "display": resolution,
                "ram": ram.get("total"),
                "storage": storage.get("total"),
                "chipset": chipset_raw or soc_model,
                "battery_level": battery.get("level"),
                "battery_health": battery.get("health"),
                "refresh_rate": refresh_rate,
                "storage_speed_mbs": storage_speed,
            }

            device_info = {"brand": brand, "model": model, "codename": chipset_raw or soc_model}
            comparisons = compare_device(scanned_for_compare, official, device_info)
            trust_score = _compute_trust_score(comparisons, verified)

            display_chipset = chipset_raw
            if official.get("chipset") not in (None, "", "N/A"):
                display_chipset = official.get("chipset")

            # Yield details of checks
            for feature, comp in comparisons.items():
                flag = comp.get("flag", "unknown")
                status_symbol = "✓" if flag == "ok" else ("⚠️" if flag == "warn" else "❌")
                message = comp.get("message", "")
                yield sse("stdout", {"text": f"  {status_symbol} {feature.upper()}: {message} (status: {flag})"})

            yield sse("success", {"text": f"Comparison done. Trust Score: {trust_score if trust_score is not None else 'N/A'}/10."})
            time.sleep(0.05)

            # Build full JSON payload for final output
            result_payload = {
                "device": {
                    "brand": brand,
                    "model": model,
                    "android": android,
                    "chipset": display_chipset,
                    "codename": chipset_raw,
                    "soc_model": soc_model or "N/A",
                },
                "battery": battery,
                "display": {"resolution": resolution, "refresh_rate": refresh_rate},
                "ram": ram,
                "storage": {**storage, "speed_mbs": storage_speed},
                "sensors": sensors,
                "official": official,
                "comparisons": comparisons,
                "trust_score": trust_score,
                "verification_status": "verified" if verified else "unverified",
            }
            
            yield sse("step", {"name": "cmp", "status": "done", "p": "100%"})
            yield sse("result", {"data": result_payload})
        except Exception as e:
            tb = traceback.format_exc()
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(tb)
            yield sse("err", {"text": f"Fatal scan error: {str(e)}"})

    return Response(generate(), mimetype="text/event-stream")


@app.route("/audit_apps")
def audit_apps():
    devices = list_adb_devices()
    if not devices:
        return jsonify({"error": "No USB device detected."}), 400
    if len(devices) > 1:
        return jsonify({"error": "Multiple devices connected."}), 400

    raw_packages = run_adb("pm list packages -3", devices[0])
    if not raw_packages:
        return jsonify({"security_audit": "No third-party apps found on this device."})

    api_key = os.getenv("FEATHERLESS_API_KEY", "").strip()
    if not api_key:
        return jsonify({"error": "Missing FEATHERLESS_API_KEY in environment variables."}), 500

    packages = [p for p in raw_packages.splitlines() if p.strip()]
    package_text = "\n".join(packages[:150])
    if len(packages) > 150:
        package_text += f"\n... and {len(packages) - 150} more packages"

    client = OpenAI(base_url="https://api.featherless.ai/v1", api_key=api_key)
    prompt = f"""You are an Android security analyst. Review these user-installed app packages and flag anything suspicious.

Packages ({len(packages)} total):
{package_text}

Rules:
1. Call out known spyware, stalkerware, or risky package names.
2. Note if anything looks like a sideloaded clone or data-harvesting tool.
3. Keep the answer under 4 sentences. Plain text only, no markdown."""

    try:
        response = client.chat.completions.create(
            model=FEATHERLESS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250,
        )
        return jsonify({"security_audit": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": f"AI engine error: {str(e)}"}), 502


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
