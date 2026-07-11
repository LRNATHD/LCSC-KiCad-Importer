import sys
import os
import ctypes
import traceback

# --- Step 1: Hide the console window immediately (before any output) ---
# We build WITHOUT --windowed so stdout/stderr work for logging,
# then hide the console via the Win32 API so the user doesn't see a black box.
def _hide_console():
    if getattr(sys, 'frozen', False):
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass

_hide_console()


# --- Step 2: Emergency crash logger (works even if stdout is broken) ---
def _emergency_log(msg):
    try:
        log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), "crash.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


# --- Step 3: Redirect stdout/stderr to daemon.log when frozen ---
class _Unbuffered:
    """Wrapper that flushes after every write so daemon.log is always up-to-date."""
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def flush(self):
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

def _setup_logging():
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
        log_file = os.path.join(log_dir, "daemon.log")
        f = open(log_file, "w", encoding="utf-8")
        sys.stdout = _Unbuffered(f)
        sys.stderr = sys.stdout

_setup_logging()


# ============================================================================
# Main application (wrapped in try/except so crashes are always logged)
# ============================================================================
try:
    import keyboard
    import threading
    import re
    import uuid
    import pyperclip

    from browser_reader import get_active_chrome_info, extract_lcsc_part_number
    from part_downloader import download_part
    from config_manager import HOTKEY, LIBRARY_DIR, SYMBOL_LIB
    from tray_icon import start_tray_icon, show_notification

    # Thread lock to prevent concurrent overlapping hotkey triggers
    _trigger_lock = threading.Lock()

    def _on_trigger():
        """Called when the global hotkey is pressed."""
        if not _trigger_lock.acquire(blocking=False):
            return

        try:
            print("\n" + "=" * 50)
            print("[+] Hotkey triggered! Scanning Chrome windows...")
            print("=" * 50)
            show_notification("Scanning Chrome tabs...", "Importer Started")

            # 1. Find an LCSC tab in Chrome
            title, url = get_active_chrome_info()
            if not title and not url:
                show_notification("No Chrome windows detected.", "Error")
                print("[-] No open Chrome windows detected.")
                return

            print(f"[i] Chrome window: '{title}'")
            if url:
                print(f"[i] Tab URL: '{url}'")

            # 2. Extract LCSC Part Number (Cxxxxx)
            part_number = extract_lcsc_part_number(title, url)
            if not part_number:
                show_notification("No LCSC part number found in Chrome.", "Error")
                print("[-] No LCSC part number found.")
                return

            print(f"[+] Found part: {part_number}")

            # 3. Download and convert via JLC2KiCadLib
            success, symbol_name, symbol_block, attributes = download_part(part_number, url)
            if not success or not symbol_name or not symbol_block:
                show_notification("Failed to download or convert the part.", "Error")
                print("[-] Download/convert failed.")
                return

            print(f"[+] Symbol retrieved: {symbol_name}")

            # Get auto-scraped keywords from LCSC
            auto_keywords = ""
            default_name = symbol_name
            if isinstance(attributes, dict):
                auto_keywords = attributes.get('_keywords', '')
                # Use Mfr.Part # as default name since it's the actual part name
                mfr_part = attributes.get('Mfr.Part #', '') or attributes.get('MFR.Part #', '') or attributes.get('Mfr. Part #', '')
                if mfr_part.strip():
                    default_name = mfr_part.strip()

            # Prompt user for custom name + keywords
            import tkinter as tk
            
            class ImportDialog(tk.Toplevel):
                def __init__(self, default_name, default_keywords):
                    self.result_name = None
                    self.result_keywords = None
                    self.cancelled = True
                    
                    root = tk.Tk()
                    root.withdraw()
                    
                    super().__init__(root)
                    self.title("LCSC Importer")
                    self.attributes('-topmost', True)
                    self.resizable(False, False)
                    self.protocol("WM_DELETE_WINDOW", self._on_cancel)
                    
                    frame = tk.Frame(self, padx=15, pady=10)
                    frame.pack(fill=tk.BOTH, expand=True)
                    
                    tk.Label(frame, text=f"Importing: {part_number}", font=("Arial", 10, "bold")).pack(anchor="w")
                    tk.Label(frame, text="").pack()  # spacer
                    
                    tk.Label(frame, text="Symbol Name (blank = default):").pack(anchor="w")
                    self.name_entry = tk.Entry(frame, width=50)
                    self.name_entry.insert(0, default_name)
                    self.name_entry.pack(fill=tk.X, pady=(0, 8))
                    self.name_entry.select_range(0, tk.END)
                    
                    tk.Label(frame, text="Keywords (space-separated):").pack(anchor="w")
                    self.kw_entry = tk.Entry(frame, width=50)
                    self.kw_entry.insert(0, default_keywords)
                    self.kw_entry.pack(fill=tk.X, pady=(0, 12))
                    
                    btn_frame = tk.Frame(frame)
                    btn_frame.pack(fill=tk.X)
                    tk.Button(btn_frame, text="Cancel", width=10, command=self._on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
                    tk.Button(btn_frame, text="Import", width=10, command=self._on_ok, bg="#4CAF50", fg="white").pack(side=tk.RIGHT)
                    
                    self.name_entry.focus_set()
                    self.bind("<Return>", lambda e: self._on_ok())
                    self.bind("<Escape>", lambda e: self._on_cancel())
                    
                    # Center on screen
                    self.update_idletasks()
                    w, h = self.winfo_width(), self.winfo_height()
                    x = (self.winfo_screenwidth() // 2) - (w // 2)
                    y = (self.winfo_screenheight() // 2) - (h // 2)
                    self.geometry(f"+{x}+{y}")
                    
                    self._root = root
                    self.grab_set()
                    self.wait_window(self)
                
                def _on_ok(self):
                    raw_name = self.name_entry.get().strip()
                    # Sanitize symbol name: KiCad S-expressions break on quotes, parentheses, etc.
                    # Replace anything that isn't alphanumeric, space, dot, dash, or underscore with an underscore.
                    self.result_name = re.sub(r'[^a-zA-Z0-9 .\-_]', '_', raw_name) if raw_name else ""
                    self.result_keywords = self.kw_entry.get().strip()
                    self.cancelled = False
                    self.destroy()
                    self._root.destroy()
                
                def _on_cancel(self):
                    self.destroy()
                    self._root.destroy()
            
            dlg = ImportDialog(default_name, auto_keywords)
            
            if dlg.cancelled:
                # User cancelled — remove the downloaded files
                print("[-] Import cancelled by user.")
                show_notification("Import cancelled.", "Cancelled")
                # Clean up the symbol that was already merged
                sym_path = os.path.join(LIBRARY_DIR, "Symbols", f"{SYMBOL_LIB}.kicad_sym")
                if os.path.exists(sym_path):
                    with open(sym_path, "r", encoding="utf-8") as f:
                        sym_content = f.read()
                    # Remove the symbol block we just added
                    pattern = rf'\n\s*\(symbol "{re.escape(symbol_name)}"'
                    match_sym = re.search(pattern, sym_content)
                    if match_sym:
                        start = match_sym.start()
                        paren_count = 0
                        end_idx = -1
                        in_q = False
                        esc = False
                        for i in range(start, len(sym_content)):
                            c = sym_content[i]
                            if esc: esc = False; continue
                            if c == '\\': esc = True; continue
                            if c == '"': in_q = not in_q; continue
                            if not in_q:
                                if c == '(': paren_count += 1
                                elif c == ')':
                                    paren_count -= 1
                                    if paren_count == 0:
                                        end_idx = i + 1; break
                        if end_idx != -1:
                            sym_content = sym_content[:start] + sym_content[end_idx:]
                            with open(sym_path, "w", encoding="utf-8") as f:
                                f.write(sym_content)
                            print("[+] Cleaned up cancelled symbol from library.")
                return

            user_keywords = dlg.result_keywords or ""
            custom_name = dlg.result_name or ""

            # Inject ki_keywords into the symbol block
            if user_keywords:
                kw_escaped = user_keywords.replace('"', '\\"')
                # Check if ki_keywords already exists
                if re.search(r'\(property\s+"ki_keywords"', symbol_block):
                    symbol_block = re.sub(
                        r'\(property\s+"ki_keywords"\s+"[^"]*"',
                        f'(property "ki_keywords" "{kw_escaped}"',
                        symbol_block
                    )
                else:
                    # Insert after the last property
                    last_prop = list(re.finditer(r'\(property\s+"[^"]+"\s+"[^"]*".*?\)', symbol_block, re.DOTALL))
                    if last_prop:
                        insert_idx = last_prop[-1].end()
                        new_prop = f'\n    (property "ki_keywords" "{kw_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                        symbol_block = symbol_block[:insert_idx] + new_prop + symbol_block[insert_idx:]

                # Also update the on-disk library file
                sym_path = os.path.join(LIBRARY_DIR, "Symbols", f"{SYMBOL_LIB}.kicad_sym")
                if os.path.exists(sym_path):
                    with open(sym_path, "r", encoding="utf-8") as f:
                        sym_content = f.read()
                    if re.search(rf'\(symbol\s+"{re.escape(symbol_name)}"', sym_content):
                        if re.search(r'\(property\s+"ki_keywords"', sym_content):
                            sym_content = re.sub(
                                r'\(property\s+"ki_keywords"\s+"[^"]*"',
                                f'(property "ki_keywords" "{kw_escaped}"',
                                sym_content
                            )
                        else:
                            # Find last property inside this symbol and insert after it
                            last_prop_disk = list(re.finditer(r'\(property\s+"[^"]+"\s+"[^"]*".*?\)', sym_content, re.DOTALL))
                            if last_prop_disk:
                                insert_idx = last_prop_disk[-1].end()
                                new_prop = f'\n    (property "ki_keywords" "{kw_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                                sym_content = sym_content[:insert_idx] + new_prop + sym_content[insert_idx:]
                        with open(sym_path, "w", encoding="utf-8") as f:
                            f.write(sym_content)
                print(f"[+] Keywords set: {user_keywords}")

            # Rename symbol if user provided a custom name
            if custom_name and custom_name != symbol_name:
                # Update the .kicad_sym file on disk
                sym_path = os.path.join(LIBRARY_DIR, "Symbols", f"{SYMBOL_LIB}.kicad_sym")
                if os.path.exists(sym_path):
                    with open(sym_path, "r", encoding="utf-8") as f:
                        sym_content = f.read()
                        
                    # Replace the root symbol and any derived symbols (extends)
                    sym_content = re.sub(rf'\(symbol "{re.escape(symbol_name)}"', f'(symbol "{custom_name}"', sym_content)
                    sym_content = re.sub(rf'\(extends "{re.escape(symbol_name)}"', f'(extends "{custom_name}"', sym_content)
                    # Replace the prefix in any child units
                    sym_content = re.sub(rf'\(symbol "{re.escape(symbol_name)}_(\d+)_(\d+)"', f'(symbol "{custom_name}_\\1_\\2"', sym_content)
                    
                    with open(sym_path, "w", encoding="utf-8") as f:
                        f.write(sym_content)
                
                # Update the clipboard payload variables
                symbol_block = re.sub(rf'\(symbol "{re.escape(symbol_name)}"', f'(symbol "{custom_name}"', symbol_block)
                symbol_block = re.sub(rf'\(extends "{re.escape(symbol_name)}"', f'(extends "{custom_name}"', symbol_block)
                symbol_block = re.sub(rf'\(symbol "{re.escape(symbol_name)}_(\d+)_(\d+)"', f'(symbol "{custom_name}_\\1_\\2"', symbol_block)
                symbol_name = custom_name
                print(f"[+] Symbol renamed to: {symbol_name}")

            print("\n" + "*" * 60)
            print(f"[+] SUCCESS: '{symbol_name}' is now in the library!")
            print(f"    You can find it in KiCad under LCSC_Imports:{symbol_name}")
            print("*" * 60 + "\n")
            show_notification(f"Downloaded {symbol_name}!\nAdded to KiCad Library.", "Success")

        except Exception as e:
            show_notification(f"Error: {e}", "Error")
            print(f"[-] Error: {e}")
            _emergency_log(f"Trigger error: {e}\n{traceback.format_exc()}")
        finally:
            _trigger_lock.release()


    def main():
        print("=" * 60)
        print("  LCSC to KiCad Importer V3 (Background Daemon)")
        print("=" * 60)
        print(f"  Hotkey: {HOTKEY.upper()}")
        print("-" * 60)

        # Register the global hotkey
        keyboard.add_hotkey(HOTKEY, _on_trigger)
        print(f"[+] Hotkey '{HOTKEY}' registered successfully.")

        # Start the system tray icon in a DAEMON THREAD.
        # This is critical: pystray.Icon.run() blocks, but on a console-subsystem exe
        # it can exit immediately. By running it in a daemon thread, the main thread
        # stays alive via keyboard.wait() which properly pumps the low-level hook.
        tray_thread = threading.Thread(target=start_tray_icon, daemon=True)
        tray_thread.start()
        print("[+] System tray icon started.")

        # Block the main thread with a proper Windows message pump.
        # The keyboard library uses SetWindowsHookEx for global hotkeys,
        # which REQUIRES the installing thread to pump Windows messages.
        # Without this, the hook callback never fires.
        print("[+] Daemon is running. Press the hotkey to import a part.\n")
        
        import ctypes
        from ctypes import wintypes
        
        msg = wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))


    if __name__ == "__main__":
        main()

except Exception as e:
    _emergency_log(f"FATAL STARTUP ERROR:\n{traceback.format_exc()}")
    sys.exit(1)
