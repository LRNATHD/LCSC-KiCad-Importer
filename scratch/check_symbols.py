import re

filepath = r'C:\Users\Noahs\My Drive\computers\Kicad_Bits\Symbols\LCSC_Imports.kicad_sym'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find all top-level symbols
new_content = content
for m in re.finditer(r'\(symbol\s+\"([^\"]+)\"[\s\S]*?\(symbol\s+\"([^\"]+)_[0-9]+_[0-9]+\"', content):
    sym_name = m.group(1)
    unit_prefix = m.group(2)
    # Be careful not to match across different symbols
    if unit_prefix != sym_name:
        print(f'Fixing {sym_name} -> {unit_prefix}')
        old_decl = f'(symbol "{sym_name}"'
        new_decl = f'(symbol "{unit_prefix}"'
        new_content = new_content.replace(old_decl, new_decl)

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Fixed symbols library.')
else:
    print('No changes needed.')
