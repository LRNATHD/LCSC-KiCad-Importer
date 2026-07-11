import re

symbol_name = "FPC-0_5FX-37PH20"
custom_name = "37pin .5mm"
SYMBOL_LIB = "LCSC_Imports"

symbol_block = """
  (symbol "FPC-0_5FX-37PH20"
    (symbol "FPC-0_5FX-37PH20_0_1"
"""

# 1. First rename operations
symbol_block = re.sub(rf'\(symbol "{re.escape(symbol_name)}"', f'(symbol "{custom_name}"', symbol_block)
symbol_block = re.sub(rf'\(extends "{re.escape(symbol_name)}"', f'(extends "{custom_name}"', symbol_block)
symbol_block = re.sub(rf'\(symbol "{re.escape(symbol_name)}_(\d+)_(\d+)"', f'(symbol "{custom_name}_\\1_\\2"', symbol_block)

print("AFTER RENAME:")
print(symbol_block)

# 2. Add library prefix
modified_symbol_block = re.sub(
    r'^\s*\(symbol\s+"([^"]+)"',
    lambda m: f'(symbol "{SYMBOL_LIB}:{m.group(1)}"',
    symbol_block,
    count=1,
    flags=re.MULTILINE
)

print("AFTER PREFIX:")
print(modified_symbol_block)
