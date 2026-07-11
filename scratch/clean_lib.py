import re
import os

lib_path = r'C:\Users\Noahs\My Drive\computers\Kicad_Bits\Symbols\LCSC_Imports.kicad_sym'

with open(lib_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(lib_path + '.backup', 'w', encoding='utf-8') as f:
    f.write(content)

# We want to remove any symbol that has "37pin", "37 pin", or "FPC-0" in its name.
# Or better, just parse the symbols and only keep the good ones.
good_symbols = ["STM8S003F3P6TR", "RP2040", "FPC-05F-24PH20", "VL53L5CXV0GC{slash}1", "VL53L5CXV0GC/1"]

# The file format is:
# (kicad_symbol_lib (version ...) (generator ...)
#   (symbol "Name" ... )
#   (symbol "Name" ... )
# )

# Regex to extract all top-level symbols
# A top-level symbol starts with `  (symbol "Name"` and ends when the parens balance.
symbols = []

pos = 0
while True:
    match = re.search(r'\n  \(symbol\s+"([^"]+)"', content[pos:])
    if not match:
        break
    
    start_idx = pos + match.start() + 1 # +1 to skip the \n
    name = match.group(1)
    
    # Find the end of this symbol block by balancing parentheses
    paren_count = 0
    in_str = False
    esc = False
    
    i = start_idx
    while i < len(content):
        c = content[i]
        if esc:
            esc = False
        elif c == '\\':
            esc = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c == '(':
                paren_count += 1
            elif c == ')':
                paren_count -= 1
                if paren_count == 0:
                    break
        i += 1
    
    end_idx = i + 1
    sym_block = content[start_idx:end_idx]
    symbols.append((name, sym_block))
    pos = end_idx

# Now reconstruct the file with only the good symbols
header_match = re.match(r'(.*?)\n  \(symbol', content, re.DOTALL)
if header_match:
    header = header_match.group(1) + "\n"
else:
    header = '(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n'

footer = ")\n"

new_content = header
for name, block in symbols:
    if "37pin" in name.lower() or "37 pin" in name.lower() or "fpc-0.5" in name.lower() or "fpc-0_5" in name.lower() or "connector" in name.lower():
        print(f"Removing corrupted symbol: {name}")
    else:
        print(f"Keeping symbol: {name}")
        new_content += block + "\n"
new_content += footer

with open(lib_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Library cleaned!")
