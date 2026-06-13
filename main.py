import keyboard
import time
import sys
from browser_reader import get_active_chrome_info, extract_lcsc_part_number
from part_downloader import download_part
from config_manager import HOTKEY, get_base_dir

import threading

# Thread lock to prevent concurrent overlapping hotkey triggers
trigger_lock = threading.Lock()

def on_trigger():
    # Attempt to acquire lock atomically and non-blockingly
    acquired = trigger_lock.acquire(blocking=False)
    if not acquired:
        return
        
    try:
        print("\n" + "="*50)
        print("[+] Hotkey triggered! Scanning background Chrome windows...")
        print("="*50)
        
        # 1. Read Chrome Active Tab Information from foreground OR background Chrome windows
        title, url = get_active_chrome_info()
        if not title and not url:
            print("[-] No open Google Chrome windows detected.")
            return
            
        print(f"[i] Inspected Chrome Window: '{title}'")
        if url:
            print(f"[i] Inspected Tab URL:       '{url}'")
            
        # 2. Extract LCSC Part Number (Cxxxxx)
        part_number = extract_lcsc_part_number(title, url)
        if not part_number:
            print("[-] Could not find an LCSC part number (Cxxxxx) in any Chrome windows/tabs.")
            print("    Please open Chrome to an LCSC product details page and try again.")
            return
            
        print(f"[+] Target LCSC Component Found: {part_number}")
        
        # 3. Download and convert the part using JLC2KiCadLib (passing the active tab URL for rich scraping)
        success, symbol_name, symbol_block, attributes = download_part(part_number, url)
        if not success or not symbol_name or not symbol_block:
            print("[-] Failed to download, convert, or post-process the part.")
            return
            
        print(f"[+] Part library files retrieved: {symbol_name}")
        
        # 4. Generate the exact KiCad 10 clipboard payload
        clean_name = symbol_name.replace('{slash}', '/')
        import uuid
        import pyperclip
        import re
        
        # We need to prepend the library nickname "EasyEDA:" to the root symbol
        # definition inside the lib_symbols block so it matches the instance lib_id perfectly.
        modified_symbol_block = re.sub(
            r'^\(symbol\s+"([^"]+)"', 
            r'(symbol "EasyEDA:\1"', 
            symbol_block.strip()
        )
        
        # Extract the designator prefix (e.g., "R", "C", "U") from the symbol definition
        ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', modified_symbol_block)
        reference_prefix = ref_match.group(1) if ref_match else "U"
        
        # This matches the KiCad 10 schematic clipboard format perfectly!
        clipboard_text = f"""(lib_symbols
  {modified_symbol_block}
)
(symbol
  (lib_id "EasyEDA:{clean_name}")
  (at 0 0 0)
  (unit 1)
  (body_style 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (in_pos_files yes)
  (dnp no)
  (fields_autoplaced yes)
  (uuid "{str(uuid.uuid4())}")
  (property "Reference" "{reference_prefix}"
    (at 0 0 0)
    (effects (font (size 1.27 1.27)))
  )
)"""
        pyperclip.copy(clipboard_text)
        
        print("\n" + "*"*60)
        print(f"[+] SUCCESS: Downloaded '{clean_name}' and formatted for KiCad 10 clipboard!")
        print(f"[i] The component is now on your clipboard and ready to place.")
        print(f"    1. Switch to KiCad Schematic Editor.")
        print(f"    2. Press 'Ctrl + V' to paste it instantly!")
        print("*"*60 + "\n")
            
    except Exception as e:
        print(f"[-] Unexpected error during trigger workflow: {e}")
    finally:
        trigger_lock.release()

import os
from tray_icon import start_tray_icon

def setup_logging():
    if getattr(sys, 'frozen', False):
        log_file = os.path.join(get_base_dir(), "daemon.log")
        sys.stdout = open(log_file, "w", encoding="utf-8")
        sys.stderr = sys.stdout

def main():
    setup_logging()
    print("=" * 60)
    print("      LCSC to KiCad Importer V3 (Instant Background Placer)")
    print("=" * 60)
    print(f" [Background Daemon Started]")
    print(f" Listening globally for hotkey: {HOTKEY.upper()}")
    print("-" * 60)
    
    # Register the hotkey callback
    keyboard.add_hotkey(HOTKEY, on_trigger)
    
    # Start the system tray icon (blocking loop)
    start_tray_icon()

if __name__ == "__main__":
    main()
