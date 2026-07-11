import re

with open(r'C:\Users\Noahs\My Drive\computers\Kicad_Bits\Symbols\LCSC_Imports.kicad_sym', 'r', encoding='utf-8') as f:
    content = f.read()

symbols = re.findall(r'^\s*\(symbol\s+"([^"]+)"', content, re.MULTILINE)
print(f"Total root symbols: {len(symbols)}")
for s in symbols:
    print(f" - {s}")
