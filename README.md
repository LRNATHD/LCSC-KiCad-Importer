# LCSC to KiCad Importer V3 (Instant Background Placer)

A background daemon that allows you to instantly import components from LCSC into your KiCad 10 schematic with a simple global hotkey.

No more manually downloading zip files, managing `.kicad_sym` files, or refreshing KiCad's library tables. Just browse LCSC, press `Ctrl+Shift+D`, and paste the component directly onto your KiCad cursor.

## Features
- **Global Hotkey:** Works while you are browsing Google Chrome.
- **Auto-Scraping:** Automatically extracts the part number and attributes from your active LCSC tab.
- **Native Clipboard Injection:** Generates a perfect KiCad 10 clipboard S-expression.
- **Library Integration:** Saves the 3D model, footprint, and symbol directly to your local library for future use.

## Prerequisites
- **Python 3.8+**
- **Google Chrome** (used for reading the active LCSC tab)
- **KiCad 8+ / 10**

## Installation

1. **Clone or Download** this repository.
2. **Install Python Dependencies:**
   Open a terminal in the project directory and run:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure your Library Path:**
   Open `config.py` in a text editor and update `LIBRARY_DIR` to point to the directory where you want to save your downloaded footprints and 3D models.
   ```python
   LIBRARY_DIR = r"C:\Users\YourName\Documents\KiCad\Libraries"
   ```

## Usage

1. Start the background daemon by running:
   ```bash
   python main.py
   ```
2. Open Google Chrome and navigate to an LCSC component page (e.g. `https://www.lcsc.com/product-detail/...`).
3. Press **`Ctrl+Shift+D`** (or your custom hotkey).
   - You will see the terminal download the component, generate the 3D footprint, and copy it to your clipboard.
4. Switch to your KiCad Schematic Editor.
5. Press **`Ctrl+V`** to paste the component instantly.

## How it works
This tool relies on [JLC2KiCadLib](https://github.com/TousstNicolas/JLC2KiCad_lib) to fetch the raw symbol and 3D step files from EasyEDA. It then intercepts the generated `.kicad_sym` data, injects rich attributes scraped directly from the LCSC webpage, and constructs a native KiCad schematic S-expression to inject it straight into your system clipboard.

## Troubleshooting
- **Cloudflare Blocks:** If JLC2KiCadLib fails to connect, Cloudflare might be blocking requests from your IP. Wait a few minutes or switch networks.
- **Chrome Accessibility:** Ensure Chrome is the active window or visible when you trigger the hotkey, as the script uses UI automation to read the active tab URL.
