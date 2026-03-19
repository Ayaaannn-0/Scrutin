# Scrutin 🛡️
### Know what's inside your phone

A consumer tool to detect fake or replaced phone components after repair.
No trust — only data.

---

## The Problem
Every day millions of people get cheated at repair shops with fake or cheap replacement components. There's no way for a normal person to verify if the parts used are genuine.

## The Solution
Scrutin scans your phone's hardware via ADB, fetches official specs from GSMArena, compares them, and flags anything suspicious — in plain language anyone can understand.

## Features
- 🔍 **Full Hardware Scan** — battery, storage, RAM, display, chipset
- 📊 **Component Comparison** — real data vs official specs
- ⚠️ **Fraud Detection** — flags suspicious or replaced components
- 💾 **Specs Cache** — fetches once, stores locally for speed
- 🌐 **Auto Spec Fetching** — works for any Android phone automatically
- 🛡️ **Precautions Guide** — how to stay safe at repair shops

## Tech Stack
- **Python** — core scanner and comparison logic
- **Flask** — REST API backend
- **ADB** — Android Debug Bridge for hardware data
- **GSMArena** — official specs source
- **Groq AI** — intelligent spec fetching
- **HTML/CSS/JS** — frontend UI

## Setup
1. Install Python from python.org
2. Download ADB platform tools and add to PATH
3. Install dependencies:
```
pip install flask flask-cors requests beautifulsoup4 groq python-dotenv
```
4. Create `.env` file with your Groq API key:
```
GROQ_API_KEY=your_key_here
```
5. Enable USB Debugging on your Android phone
6. Connect phone via USB
7. Run the app:
```
python app.py
```
8. Open `scrutin.html` in your browser

## Project Status
🚧 Active development — v0.1 prototype

## Built By
Ayaan
