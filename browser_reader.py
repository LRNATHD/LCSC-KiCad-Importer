import uiautomation as auto
import re

def get_active_chrome_info():
    """
    Scans all open Chrome windows (both foreground and background/minimized).
    Returns (title, url) of the first Chrome window that successfully contains an LCSC part number (Cxxxxx).
    
    If no direct part number is found in any Chrome window titles/URLs, it returns the first window containing
    the word "lcsc" or falls back to the currently focused Chrome window.
    """
    lcsc_pattern = r'\b(C\d{3,8})\b'
    
    # Initialize COM / UIAutomation context for the current executing thread
    with auto.UIAutomationInitializerInThread(debug=False):
        try:
            # Get desktop root control
            root = auto.GetRootControl()
            windows = root.GetChildren()
            
            fallback_candidates = []
            
            for win in windows:
                # Chrome windows have class name 'Chrome_WidgetWin_1'
                if win.ClassName == 'Chrome_WidgetWin_1':
                    title = win.Name
                    if not title:
                        continue
                    
                    url = None
                    try:
                        # Attempt to extract URL silently from address bar
                        address_bar = win.EditControl(Name='Address and search bar')
                        if not address_bar.Exists(0, 0):
                            address_bar = win.EditControl(searchDepth=8)
                        if address_bar and address_bar.Exists(0, 0):
                            url = address_bar.GetValuePattern().Value
                    except Exception:
                        pass
                    
                    # Prioritize finding the actual part number (Cxxxxx) in title or URL
                    has_part_in_url = url and re.search(lcsc_pattern, url, re.IGNORECASE)
                    has_part_in_title = title and re.search(lcsc_pattern, title, re.IGNORECASE)
                    
                    if has_part_in_url or has_part_in_title:
                        print(f"[i] Found active LCSC part tab: '{title}'")
                        return title, url
                        
                    # Lower priority: Just matches the keyword "lcsc"
                    if "lcsc" in title.lower():
                        fallback_candidates.append((title, url))
            
            # If we didn't find an explicit part number, return the first lcsc-themed window
            if fallback_candidates:
                return fallback_candidates[0]
                
            # Final fallback: Look at the active foreground Chrome window if any
            fg = auto.GetForegroundWindow()
            if fg and fg.ClassName == 'Chrome_WidgetWin_1':
                title = fg.Name
                url = None
                try:
                    address_bar = fg.EditControl(Name='Address and search bar')
                    if not address_bar.Exists(0, 0):
                        address_bar = fg.EditControl(searchDepth=8)
                    if address_bar and address_bar.Exists(0, 0):
                        url = address_bar.GetValuePattern().Value
                except Exception:
                    pass
                return title, url
                
        except Exception as e:
            print(f"[-] Error scanning background Chrome windows: {e}")
            
    return None, None

def extract_lcsc_part_number(title, url):
    """
    Given the tab title and/or URL, extracts the LCSC part number (e.g. C11702).
    """
    # Regex to find LCSC part numbers (C followed by 3 to 8 digits)
    # e.g., C11702, C204859, C3001
    lcsc_pattern = r'\b(C\d{3,8})\b'
    
    # 1. Search in URL
    if url:
        match = re.search(lcsc_pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
            
    # 2. Search in Title
    if title:
        match = re.search(lcsc_pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).upper()
            
    return None

if __name__ == "__main__":
    print("Scanning for Chrome windows (including in the background)...")
    title, url = get_active_chrome_info()
    print(f"Extracted Title: {title}")
    print(f"Extracted URL: {url}")
    part = extract_lcsc_part_number(title, url)
    print(f"Extracted Part Number: {part}")
