import re

lib_path = r"C:\Users\Noahs\My Drive\computers\Kicad_Bits\Symbols\LCSC_Imports.kicad_sym"

with open(lib_path, "r", encoding="utf-8") as f:
    content = f.read()

# KiCad symbol definition looks like (symbol "Name" (pin_names...) (exclude_from_sim no) ... (symbol "Name_0_0" ...))
# It's a nested S-expression. The units are inside the root symbol block.
# We can just look for (symbol "RootName" and then inside it, any (symbol "RootName_X_Y".
# Actually, an easier way to fix a corrupted file where the root name was changed but the children weren't:
# The children always immediately follow the properties of the root symbol, and they end with _\d+_\d+
# Let's parse the file by root symbols.

blocks = []
current_pos = 0

def find_matching_paren(text, start_idx):
    paren_count = 0
    in_quotes = False
    escape = False
    for i in range(start_idx, len(text)):
        char = text[i]
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
                    return i
    return -1

out_content = content
changed = False

for m in re.finditer(r'\n\s*\(symbol\s+"([^"]+)"', content):
    root_name = m.group(1)
    
    # If this is already a unit name (ends in _x_y), skip it
    if re.search(r'_\d+_\d+$', root_name):
        continue
        
    start_idx = m.start()
    end_idx = find_matching_paren(content, content.find('(', start_idx))
    
    if end_idx == -1: continue
    
    block = content[start_idx:end_idx+1]
    
    # Inside this block, all child symbols should be named {root_name}_{unit}_{style}
    # But because of our bug, they might be named {old_name}_{unit}_{style}
    # Let's find all (symbol "Something_X_Y" inside the block and fix them.
    
    def replace_unit(match):
        prefix = match.group(1)
        suffix = match.group(2)
        if prefix != root_name:
            print(f"Fixing mismatched unit: {prefix}{suffix} -> {root_name}{suffix}")
            global changed
            changed = True
            return f'(symbol "{root_name}{suffix}"'
        return match.group(0)
        
    new_block = re.sub(r'\(symbol\s+"([^"]+)(_\d+_\d+)"', replace_unit, block)
    
    if new_block != block:
        out_content = out_content.replace(block, new_block)

if changed:
    with open(lib_path, "w", encoding="utf-8") as f:
        f.write(out_content)
    print("Library fixed successfully.")
else:
    print("No mismatches found.")
