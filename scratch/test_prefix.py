import re

SYMBOL_LIB = "LCSC_Imports"
symbol_block = """
  (symbol "37pin .5mm"
    (pin_names (offset 1.016))
    (symbol "37pin .5mm_0_1"
      (rectangle
      )
    )
    (symbol "37pin .5mm_1_1"
      (rectangle
      )
    )
  )
"""

modified_symbol_block = re.sub(
    r'^(\s*)\(symbol\s+"([^"]+)"',
    lambda m: f'{m.group(1)}(symbol "{SYMBOL_LIB}:{m.group(2)}"',
    symbol_block,
    flags=re.MULTILINE
)

print(modified_symbol_block)
