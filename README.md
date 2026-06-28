# Scrutin (v0.2)
### Know what's inside your phone — No trust, only data.

Scrutin is a hardware forensics and diagnostics tool designed to protect pre-owned device buyers and repair customers from fraud. It bypasses spoofed operating system menus by extracting physical metrics directly via low-level Android Debug Bridge (ADB) commands, validates them against factory registries using AI, and presents reports in plain language.

---

## 🛠️ The Problem & Solution

* **The Fraud Reality:** Scammers frequently spoof the Android settings menu to falsely display high-end specifications (e.g., displaying `8GB RAM / 256GB ROM` on screen when the underlying hardware is actually a cheap cloned `1GB RAM / 8GB ROM` chip). Standard diagnostic apps (like CPU-Z or DevCheck) blindly trust local software APIs.
* **The Scrutin Defense:** By connecting the phone via USB, Scrutin queries the hardware registers directly (e.g., `/proc/meminfo`, raw partitions descriptors, system build flags), bypasses spoofed OS wrappers, and validates the extracted values against factory registries (cross-referencing specs via Featherless AI and MobileAPI fallbacks).

---

## 💎 Features & Diagnostic visualizers

### 1. Interactive 2D Motherboard SVG Mockup
* **Interactive Tooltip specs:** Hovering over individual chips (SCREEN, RAM, STORAGE, PROCESSOR, BATTERY, SENSORS) on the circuit board shows live specs and validation status (Verified/Mismatch/Unverified) instantly.
* **Component highlights:** Highlights corresponding diagnostic cards in real-time on hover, mapping hardware logs to visual components.

### 2. 3D Smartphone Device Mockup
* **Interactive Rotation:** Follows cursor movements in real-time showing 3D roll and pitch.
* **Premium Outer Shell:** Designed with a thick titanium lavender frame and a vertical dual-lens pill camera bump with glass gradients.
* **Diagnostic Screen:** Plays a scanning green laser beam swipe animation during audits.

### 3. Detailed Hardware Visualizers
* **🔋 Battery Subsystem:** Features a 3D glass cylinder with animated bubbles and a fluid wave indicating charge level. Includes status cards for level, health, chemistry, voltage (with adapter-voltage filtering), and cycle count resets.
* **⚙️ CPU dial gauge:** Animates clock speeds up to max GHz using a speedometer dial accompanied by an active multi-core grid chip.
* **💾 Storage:** Shows a radial progress ring chart of utilized storage space.
* **🧠 RAM Oscilloscope:** Draws real-time memory activity sweeps on an HTML5 canvas relative to current RAM consumption pressure.
* **🖥️ Display Calibrator:** Toggles frame rates (60Hz vs 30Hz step animations) and renders an active color calibration canvas matrix.
* **🧭 Sensors (Gyroscope):** Renders a wireframe 3D gyroscope box rotating in real-time according to mouse movements, displaying precise Roll, Pitch, and Yaw values.

### 4. Before / After Repair Comparison
* Compare snapshots of a device before sending it to a repair shop and after it returns.
* Flags anomalies like battery cycle count resets, RAM component swaps, display modifications, or storage write speed drops (>50 MB/s).

### 5. App Privacy & Malware Audit
* Scans third-party application package signatures via the Featherless application auditing engine, flagging suspicious permissions or risk profiles.

### 6. Real-time Design Theme Switcher
* Switch themes dynamically via the 🎨 menu button in the header. Includes persistent `localStorage` settings for:
  * **🌸 Light Pearl:** Frosted white glass cards with soft lavender outlines and high-contrast charcoal text.
  * **🌌 Neon Cyberpunk:** Deep dark theme with glowing neon-green elements, cyber-purple tracks, and dark consoles.
  * **🌅 Sunset Rose:** Warm peach-pink pearlescent theme with rose gold frames and deep maroon accents.

---

## 💻 Tech Stack

* **Flask & Python:** Local web server backend communicating with ADB and compiling API specifications.
* **Vanilla CSS (Glassmorphism):** Fast, utility-free CSS styles featuring backdrop filters, mesh ambient gradients, and keyframe animations.
* **HTML5 Canvas & SVG:** High-performance vector drawings for motherboard routing tracks, CPU dials, gyroscope matrices, and oscilloscope waves.
* **Featherless AI & MobileAPI:** Cross-references device model codenames against factory specs registries to detect counterfeit clones.

---

## 🚀 Setup & Execution

### Prerequisites
1. Install Python 3.10+ from [python.org](https://python.org)
2. Download [ADB Platform Tools](https://developer.android.com/tools/releases/platform-tools) and add it to your system PATH.
3. Enable **USB Debugging** on the target Android phone (Settings -> About Phone -> tap Build Number 7 times, then go to Developer Options -> enable USB Debugging).

### Installation
1. Clone the repository and navigate to the directory:
   ```bash
   cd scrutin-0.2
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your API credentials in a `.env` file:
   ```env
   FEATHERLESS_API_KEY=your_featherless_key
   MOBILE_API_KEY=your_mobileapi_key
   ```

### Running the Application
1. Connect your Android phone to the computer via USB cable.
2. Start the local Flask web server:
   ```bash
   python app.py
   ```
3. Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

*Note: For a simple terminal-only scan output, you can run:*
```bash
python scanner.py
```
