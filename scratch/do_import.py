import sys
import os
import re
import uuid
import pyperclip

# Add the parent directory to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from part_downloader import download_part
from config_manager import LIBRARY_DIR, SYMBOL_LIB

def run_import():
    part_number = "C19077731"
    custom_name = "37pin 0.5mm pitch screen fpc connector"
    
    print(f"Downloading {part_number}...")
    success, symbol_name, symbol_block, attributes = download_part(part_number)
    
    if not success or not symbol_block:
        print("Failed to download or parse symbol block.")
        return
        
    print(f"Downloaded symbol: {symbol_name}")
    
    # Get keywords
    auto_keywords = attributes.get('_keywords', '')
    if auto_keywords:
        kw_escaped = auto_keywords.replace('"', '\\"')
        if re.search(r'\(property\s+"ki_keywords"', symbol_block):
            symbol_block = re.sub(
                r'\(property\s+"ki_keywords"\s+"[^"]*"',
                f'(property "ki_keywords" "{kw_escaped}"',
                symbol_block
            )
        else:
            last_prop = list(re.finditer(r'\(property\s+"[^"]+"\s+"[^"]*".*?\)', symbol_block, re.DOTALL))
            if last_prop:
                insert_idx = last_prop[-1].end()
                new_prop = f'\n    (property "ki_keywords" "{kw_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                symbol_block = symbol_block[:insert_idx] + new_prop + symbol_block[insert_idx:]

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
                    last_prop_disk = list(re.finditer(r'\(property\s+"[^"]+"\s+"[^"]*".*?\)', sym_content, re.DOTALL))
                    if last_prop_disk:
                        insert_idx = last_prop_disk[-1].end()
                        new_prop = f'\n    (property "ki_keywords" "{kw_escaped}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))'
                        sym_content = sym_content[:insert_idx] + new_prop + sym_content[insert_idx:]
                with open(sym_path, "w", encoding="utf-8") as f:
                    f.write(sym_content)
        print(f"Keywords set: {auto_keywords}")

    # Rename symbol
    if custom_name and custom_name != symbol_name:
        sym_path = os.path.join(LIBRARY_DIR, "Symbols", f"{SYMBOL_LIB}.kicad_sym")
        if os.path.exists(sym_path):
            with open(sym_path, "r", encoding="utf-8") as f:
                sym_content = f.read()
                
            sym_content = re.sub(rf'\(symbol "{re.escape(symbol_name)}"', f'(symbol "{custom_name}"', sym_content)
            sym_content = re.sub(rf'\(extends "{re.escape(symbol_name)}"', f'(extends "{custom_name}"', sym_content)
            
            with open(sym_path, "w", encoding="utf-8") as f:
                f.write(sym_content)
        
        symbol_block = re.sub(rf'\(symbol "{re.escape(symbol_name)}"', f'(symbol "{custom_name}"', symbol_block)
        symbol_block = re.sub(rf'\(extends "{re.escape(symbol_name)}"', f'(extends "{custom_name}"', symbol_block)
        symbol_name = custom_name
        print(f"Symbol renamed to: {symbol_name}")
        
    # Build Clipboard Payload
    clean_name = symbol_name.replace('{slash}', '/')

    modified_symbol_block = re.sub(
        r'^\(symbol\s+"([^"]+)"',
        lambda m: f'(symbol "{SYMBOL_LIB}:{m.group(1)}"',
        symbol_block,
        count=1,
        flags=re.MULTILINE
    )

    reference_prefix = attributes.get('_designator', 'U')

    modified_symbol_block = re.sub(
        r'\(property\s+"Reference"\s+"[^"]+"',
        f'(property "Reference" "{reference_prefix}"',
        modified_symbol_block
    )

    def get_normalized_at(prop_name, default_at="(at 0 0 0)"):
        match = re.search(
            rf'\(property\s+"{prop_name}".*?\(at\s+([-0-9.]+)\s+([-0-9.]+)(?:\s+([-0-9.]+))?\)',
            modified_symbol_block, re.DOTALL
        )
        if match:
            x, y, angle = match.groups()
            angle = angle if angle is not None else "0"
            return f"(at {x} {y} {angle})"
        return default_at

    ref_at = get_normalized_at("Reference", "(at 0 5.08 0)")
    fp_at = get_normalized_at("Footprint", "(at 0 0 0)")
    val_at = get_normalized_at("Value", "(at 0 6.35 0)")

    fp_match = re.search(r'\(property\s+"Footprint"\s+"([^"]+)"', modified_symbol_block)
    fp_str = fp_match.group(1) if fp_match else ""

    val_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', modified_symbol_block)
    val_str = val_match.group(1) if val_match else ""

    fp_prop = ""
    if fp_str:
        fp_prop = f"""  (property "Footprint" "{fp_str}"
    {fp_at}
    (effects (font (size 1.27 1.27)) hide)
  )"""

    val_prop = ""
    if val_str:
        val_prop = f"""  (property "Value" "{val_str}"
    {val_at}
    (effects (font (size 1.27 1.27)))
  )"""

    clipboard_text = f"""(lib_symbols
  {modified_symbol_block}
)
(symbol
  (lib_id "{SYMBOL_LIB}:{clean_name}")
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
    {ref_at}
    (effects (font (size 1.27 1.27)))
  )
{val_prop}
{fp_prop}
)"""

    pyperclip.copy(clipboard_text)
    print("DONE! The symbol is in the library and ready in the clipboard.")
    
if __name__ == "__main__":
    run_import()
