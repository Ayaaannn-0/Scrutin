# Scrutin
### Know what's inside your phone

A consumer tool to detect cheap or replaced phone components after repair.
No trust — only data.

---

## The Problem

Every day millions of people get cheated at repair shops with cheap or mismatched replacement components. There's no way for a normal person to verify if the parts used match the specifications.

## The Solution

Scrutin scans your phone's hardware via ADB, fetches official specs (Featherless AI with MobileAPI as fallback), compares them with AI-assisted validation, and flags anything suspicious — in plain language anyone can understand.

## Features

- **Full Hardware Scan** — battery, storage, RAM, display, chipset
- **Component Comparison** — scanned data vs official specs via Featherless AI
- **Fraud Detection** — flags suspicious or replaced components
- **Specs Cache** — fetches once, stores locally for speed
- **App Privacy Audit** — AI review of installed third-party apps
- **Precautions Guide** — how to stay safe at repair shops

## Tech Stack

- **Python** — core scanner and API
- **Flask** — REST API and web UI
- **ADB** — Android Debug Bridge for hardware data
- **Featherless AI** — primary spec lookup and hardware comparison
- **MobileAPI** — fallback spec source when AI lookup is insufficient

## Setup

1. Install Python from [python.org](https://python.org)
2. Download [ADB platform tools](https://developer.android.com/tools/releases/platform-tools) and add to PATH
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file (see `.env.example`):

```env
FEATHERLESS_API_KEY=your_featherless_key
MOBILE_API_KEY=your_mobileapi_key
```

5. Enable USB Debugging on your Android phone
6. Connect the phone via USB
7. Run the app:

```bash
python app.py
```

8. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser

### CLI scanner (ADB only, no AI)

```bash
python scanner.py
```

## Project Status

Active development — v0.2 prototype

