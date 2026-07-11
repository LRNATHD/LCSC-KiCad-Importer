import re
symbol_name = "FPC-0_5FX-37PH20"
custom_name = "37pin .5mm"
symbol_block = """
(symbol "FPC-0_5FX-37PH20"
  (symbol "FPC-0_5FX-37PH20_0_1"
"""
res = re.sub(rf'\(symbol "{re.escape(symbol_name)}_(\d+)_(\d+)"', f'(symbol "{custom_name}_\\1_\\2"', symbol_block)
print(res)
