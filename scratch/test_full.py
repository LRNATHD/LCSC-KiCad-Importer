import sys
import os
from part_downloader import download_part
import re
import uuid
import json

SYMBOL_LIB = "LCSC_Imports"

def test_download(part_number):
    success, symbol_name, symbol_block, attributes = download_part(part_number)
    if not success:
        print("Failed to download")
        return
        
    print(f"Downloaded: {symbol_name}")
    
    clean_name = symbol_name.replace('{slash}', '/')

    # Prefix the root symbol definition with the library nickname
    modified_symbol_block = re.sub(
        r'^\(symbol\s+"([^"]+)"',
        lambda m: f'(symbol "{SYMBOL_LIB}:{m.group(1)}"',
        symbol_block,
        count=1,
        flags=re.MULTILINE
    )

    reference_prefix = "U"

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

    def get_id(prop_name, default_id):
        match = re.search(rf'\(property\s+"{prop_name}".*?\(id\s+(\d+)\)', modified_symbol_block)
        return match.group(1) if match else str(default_id)

    ref_at = get_normalized_at("Reference", "(at 0 5.08 0)")
    fp_at = get_normalized_at("Footprint", "(at 0 0 0)")
    val_at = get_normalized_at("Value", "(at 0 6.35 0)")

    ref_id = get_id("Reference", 0)
    val_id = get_id("Value", 1)
    fp_id = get_id("Footprint", 2)

    fp_match = re.search(r'\(property\s+"Footprint"\s+"([^"]+)"', modified_symbol_block)
    fp_str = fp_match.group(1) if fp_match else ""

    val_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', modified_symbol_block)
    val_str = val_match.group(1) if val_match else ""

    fp_prop = ""
    if fp_str:
        fp_prop = f"""  (property "Footprint" "{fp_str}" (id {fp_id})
    {fp_at}
    (effects (font (size 1.27 1.27) italic) hide)
  )"""

    val_prop = ""
    if val_str:
        val_prop = f"""  (property "Value" "{val_str}" (id {val_id})
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
  (property "Reference" "{reference_prefix}" (id {ref_id})
    {ref_at}
    (effects (font (size 1.27 1.27)))
  )
{val_prop}
{fp_prop}
)"""

    print("--- CLIPBOARD PAYLOAD ---")
    print(clipboard_text)
    print("-------------------------")
    
if __name__ == "__main__":
    test_download("C19077731")
