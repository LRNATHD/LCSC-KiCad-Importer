import sys
import os
import urllib.request
import urllib.error
import requests
import re

from JLC2KiCadLib import JLC2KiCadLib
from config_manager import LIBRARY_DIR, SYMBOL_LIB, FOOTPRINT_LIB

def parse_lcsc_html_attributes(html_content):
    """
    Parses LCSC product details HTML and extracts key attributes using a row-isolated approach.
    """
    rows = re.findall(r'<tr[^>]*>.*?</tr>', html_content, re.DOTALL | re.IGNORECASE)
    extracted = {}
    
    for row in rows:
        label_match = re.search(r'<td class="font-Bold-600"[^>]*>\s*(.*?)\s*</td>', row, re.DOTALL | re.IGNORECASE)
        if not label_match:
            continue
            
        label = re.sub(r'<[^>]+>', '', label_match.group(1)).strip()
        
        tds = re.findall(r'<td[^>]*>.*?</td>', row, re.DOTALL | re.IGNORECASE)
        if len(tds) < 2:
            continue
            
        value_td = tds[1]
        
        # Strip all HTML tags to get clean plain text
        value_clean = re.sub(r'<[^>]+>', '', value_td).strip()
        value_clean = re.sub(r'\s+', ' ', value_clean).strip()
        
        extracted[label] = value_clean
        
    return extracted

def fetch_lcsc_attributes(part_number, tab_url=None):
    """
    Fetches the LCSC page HTML for a given part number and extracts attributes.
    Falls back to a standard part details page if tab_url is not provided.
    """
    url = tab_url
    if not url or not url.startswith("http"):
        url = f"https://www.lcsc.com/product-detail/{part_number}.html"
        
    print(f"[i] Fetching product attributes from LCSC: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')
            attributes = parse_lcsc_html_attributes(html)
            
            import json
            designator = "U"
            match = re.search(r'"@type":"BreadcrumbList",.*?"itemListElement":(\[.*?\])', html)
            if match:
                try:
                    breadcrumbs = json.loads(match.group(1))
                    categories = [b.get('name', '') for b in breadcrumbs]
                    text = " ".join(categories).lower()
                    if 'resistor' in text: designator = 'R'
                    elif 'capacitor' in text: designator = 'C'
                    elif 'inductor' in text or 'coil' in text or 'transformer' in text: designator = 'L'
                    elif 'diode' in text or 'rectifier' in text or 'tvs' in text or 'led' in text: designator = 'D'
                    elif 'transistor' in text or 'mosfet' in text or 'bjt' in text: designator = 'Q'
                    elif 'connector' in text or 'socket' in text or 'header' in text: designator = 'J'
                    elif 'switch' in text or 'button' in text: designator = 'SW'
                    elif 'relay' in text: designator = 'K'
                    elif 'crystal' in text or 'oscillator' in text or 'resonator' in text: designator = 'Y'
                    elif 'fuse' in text: designator = 'F'
                    elif 'antenna' in text: designator = 'ANT'
                    elif 'battery' in text: designator = 'BT'
                except Exception:
                    pass
                    
            attributes['_designator'] = designator
            
            # Build keywords from breadcrumbs, manufacturer, package, description
            keywords = set()
            if match:
                try:
                    for b in breadcrumbs:
                        name = b.get('name', '').strip()
                        if name and name.lower() not in ('home', 'lcsc', ''):
                            keywords.add(name)
                except Exception:
                    pass
            
            # Add manufacturer, package, and key attributes as keywords
            for key in ('Manufacturer', 'Package', 'Key Attributes', 'Description'):
                val = attributes.get(key, '').strip()
                if val:
                    keywords.add(val)
            
            # Add the part number itself
            keywords.add(part_number)
            
            attributes['_keywords'] = ' '.join(sorted(keywords))
            
            print(f"[+] Scraped attributes successfully: {attributes.keys()}")
            return attributes
    except Exception as e:
        print(f"[-] Scrape failed: {e}. Falling back to basic properties.")
        return {}

def extract_symbol_from_lib(lib_path, lcsc_part_number):
    """
    Parses a .kicad_sym file, locates the symbol matching the LCSC number,
    and returns (symbol_name, symbol_block).
    """
    if not os.path.exists(lib_path):
        return None, None
        
    with open(lib_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    symbols = []
    # Locate all symbol definitions in the library
    for m in re.finditer(r'\n\s*\(symbol\s+"([^"]+)"', content):
        start_idx = m.start()
        paren_count = 0
        in_quotes = False
        escape = False
        end_idx = -1
        
        for i in range(start_idx, len(content)):
            char = content[i]
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_quotes = not in_quotes
                continue
            if not in_quotes:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        end_idx = i + 1
                        break
                        
        if end_idx != -1:
            symbol_block = content[start_idx:end_idx].strip()
            symbol_name = m.group(1)
            symbols.append((symbol_name, symbol_block))
            
    # Search for the block containing our target LCSC part number (e.g. "C3178303")
    target_pattern = rf'"{lcsc_part_number}"'
    for name, block in symbols:
        if re.search(target_pattern, block, re.IGNORECASE):
            return name, block
            
    return None, None

def update_symbol_properties(symbol_block, attributes):
    """
    Injects or updates custom properties (Description, Packaging, Manufacturer)
    inside the S-expression block.
    """
    def set_property(block, name, val):
        val_escaped = val.replace('"', '\\"')
        pattern = rf'\(property\s+"{re.escape(name)}"\s+"[^"]*"\s*(.*?)\)'
        
        match = re.search(pattern, block, re.DOTALL)
        if match:
            old_prop = match.group(0)
            val_pattern = rf'\(property\s+"{re.escape(name)}"\s+"([^"]*)"'
            val_match = re.search(val_pattern, old_prop)
            if val_match:
                new_prop = old_prop.replace(f'"{val_match.group(1)}"', f'"{val_escaped}"', 1)
                return block.replace(old_prop, new_prop, 1)
        else:
            # Insert right after the Datasheet property
            datasheet_match = re.search(r'\(property\s+"Datasheet"\s+"[^"]*"\s*.*?\)', block, re.DOTALL)
            if datasheet_match:
                insert_idx = datasheet_match.end()
                new_prop = f'\n    (property "{name}" "{val_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                return block[:insert_idx] + new_prop + block[insert_idx:]
            else:
                first_line_match = re.match(r'^\s*\(symbol\s+"[^"]+"\s*', block)
                if first_line_match:
                    insert_idx = first_line_match.end()
                    new_prop = f'\n    (property "{name}" "{val_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                    return block[:insert_idx] + new_prop + block[insert_idx:]
        return block

    # Prioritize Key Attributes then Description for KiCad's Description field
    desc_val = attributes.get('Key Attributes', attributes.get('Description', ''))
    if desc_val:
        symbol_block = set_property(symbol_block, "Description", desc_val)
        
    packaging = attributes.get('Packaging', '')
    if packaging:
        symbol_block = set_property(symbol_block, "Packaging", packaging)
        
    mfr = attributes.get('Manufacturer', '')
    if mfr:
        symbol_block = set_property(symbol_block, "Manufacturer", mfr)
        
    return symbol_block

def merge_symbol_into_library(lib_path, symbol_name, symbol_block):
    """
    Appends or replaces the symbol block inside the target library file.
    """
    if not os.path.exists(lib_path):
        content = f'(kicad_symbol_lib (version 20210201) (generator TousstNicolas/JLC2KiCad_lib)\n  {symbol_block}\n)\n'
        with open(lib_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] Created fresh library and saved symbol: {lib_path}")
        return
        
    with open(lib_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    pattern = rf'\n\s*\(symbol\s+"{re.escape(symbol_name)}"'
    match = re.search(pattern, content)
    if not match:
        pattern = rf'\n\s*\(symbol\s+{re.escape(symbol_name)}'
        match = re.search(pattern, content)
        
    if match:
        start_idx = match.start()
        paren_count = 0
        in_quotes = False
        escape = False
        end_idx = -1
        for i in range(start_idx, len(content)):
            char = content[i]
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_quotes = not in_quotes
                continue
            if not in_quotes:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        end_idx = i + 1
                        break
        if end_idx != -1:
            new_content = content[:start_idx] + "\n  " + symbol_block + content[end_idx:]
            with open(lib_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"[+] Successfully updated symbol '{symbol_name}' in library: {lib_path}")
            return
            
    # Not found, append right before the last closing parenthesis
    last_paren = content.rfind(')')
    if last_paren != -1:
        new_content = content[:last_paren] + "  " + symbol_block + "\n" + content[last_paren:]
        with open(lib_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[+] Successfully merged new symbol '{symbol_name}' into library: {lib_path}")

def download_part(part_number, tab_url=None):
    """
    Invokes JLC2KiCadLib to download components, scrapes LCSC attributes,
    injects them into the S-expression, and merges it into the active root library.
    Returns (success, symbol_name, symbol_block, attributes)
    """
    if not part_number:
        print("No part number provided to downloader.")
        return False, None, None, None
    
    part_number = part_number.strip().upper()
    print(f"[+] Starting V3 download & conversion pipeline for {part_number}...")
    
    # 1. Fetch rich attributes from LCSC
    attributes = fetch_lcsc_attributes(part_number, tab_url)
    
    # 2. Invoke JLC2KiCadLib to fetch EasyEDA files (footprints, 3D shapes, symbol)
    # Ensure all target directories exist before JLC2KiCadLib runs
    os.makedirs(os.path.join(LIBRARY_DIR, "Footprints"), exist_ok=True)
    os.makedirs(os.path.join(LIBRARY_DIR, "3D_Models"), exist_ok=True)
    os.makedirs(os.path.join(LIBRARY_DIR, "Symbols"), exist_ok=True)
    
    old_argv = sys.argv
    sys.argv = [
        "JLC2KiCadLib",
        part_number,
        "-dir", LIBRARY_DIR,
        "-symbol_lib", SYMBOL_LIB,
        "-footprint_lib", FOOTPRINT_LIB,
        "-model_dir", f"../3D_Models/{FOOTPRINT_LIB}.3dshapes",
        "--skip_existing"
    ]
    
    lib_symbol_name = None
    symbol_block = None
    
    try:
        try:
            JLC2KiCadLib.main()
        except SystemExit as se:
            # Catch JLC2KiCadLib's sys.exit() call so the daemon process does not exit
            if se.code is not None and se.code != 0:
                print(f"[-] JLC2KiCadLib exited with error code: {se.code}")
                return False, None, None, None
                
        print(f"[+] JLC2KiCadLib execution complete.")
        
        # Post-process: Automatically migrate footprints to the .pretty folder inside the user's Footprints directory
        import shutil
        import re
        src_fp_dir = os.path.join(LIBRARY_DIR, FOOTPRINT_LIB)
        dst_fp_dir = os.path.join(LIBRARY_DIR, "Footprints", f"{FOOTPRINT_LIB}.pretty")
        
        # We need the absolute path to the 3dshapes folder for KiCad 3D models to work reliably
        # regardless of what project directory the user is currently in.
        abs_3d_dir = os.path.join(LIBRARY_DIR, "3D_Models", f"{FOOTPRINT_LIB}.3dshapes").replace('\\', '/')
        
        if os.path.exists(src_fp_dir):
            if not os.path.exists(dst_fp_dir):
                os.makedirs(dst_fp_dir)
            for item in os.listdir(src_fp_dir):
                s = os.path.join(src_fp_dir, item)
                d = os.path.join(dst_fp_dir, item)
                if s.endswith('.kicad_mod'):
                    # Read the footprint to fix 3D model paths
                    with open(s, 'r', encoding='utf-8') as f:
                        fp_content = f.read()
                        
                    # Fix 1: JLC2KiCadLib relative paths (e.g. "../3D_Models/LCSC_Imports.3dshapes/XYZ.step")
                    # Change to absolute paths so they work in ANY project
                    fp_content = re.sub(
                        rf'\(model\s+["\']?\.\./3D_Models/{FOOTPRINT_LIB}\.3dshapes/',
                        f'(model "{abs_3d_dir}/',
                        fp_content
                    )
                    
                    # Fix 2: Legacy EasyEDA KiCad footprint references (e.g. "${KISYS3DMOD}/...")
                    # Update to KiCad 10's environment variable
                    fp_content = fp_content.replace('${KISYS3DMOD}', '${KICAD10_3DMODEL_DIR}')
                    
                    # Write it directly to the destination
                    with open(d, 'w', encoding='utf-8') as f:
                        f.write(fp_content)
                    
                    # Remove the old source file
                    os.remove(s)
                    
            # Try to clean up the empty source directory
            try:
                os.rmdir(src_fp_dir)
            except OSError:
                pass
    

        
        # 3. Locate the symbol in JLC2KiCadLib's output symbol library (Symbol/EasyEDA.kicad_sym)
        jlc_lib_path = os.path.join(LIBRARY_DIR, "Symbol", f"{SYMBOL_LIB}.kicad_sym")
        lib_symbol_name, symbol_block = extract_symbol_from_lib(jlc_lib_path, part_number)
        
        if not lib_symbol_name or not symbol_block:
            print(f"[-] Could not find symbol for {part_number} inside {jlc_lib_path}")
            return False, None, None, None
            
        print(f"[+] Successfully located symbol definition block: '{lib_symbol_name}'")
        
        # 4. Inject LCSC attributes into the symbol block properties
        if attributes:
            symbol_block = update_symbol_properties(symbol_block, attributes)
            
        # 5. Merge the updated symbol into the active root library file
        os.makedirs(os.path.join(LIBRARY_DIR, "Symbols"), exist_ok=True)
        active_root_lib = os.path.join(LIBRARY_DIR, "Symbols", f"{SYMBOL_LIB}.kicad_sym")
        merge_symbol_into_library(active_root_lib, lib_symbol_name, symbol_block)
        
        return True, lib_symbol_name, symbol_block, attributes
        
    except Exception as e:
        print(f"[-] JLC2KiCadLib / Post-processing execution failed: {e}")
        return False, None, None, None
    finally:
        sys.argv = old_argv

if __name__ == "__main__":
    test_part = "C3178303"
    success, sym_name, sym_block, attrs = download_part(test_part)
    print(f"Success: {success}")
    print(f"Symbol Name: {sym_name}")
    print(f"Attributes: {attrs}")
