import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
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
