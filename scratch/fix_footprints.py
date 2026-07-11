import os
import re

dir_path = r'C:\Users\Noahs\My Drive\computers\Kicad_Bits\Footprints\LCSC_Imports.pretty'
for filename in os.listdir(dir_path):
    if filename.endswith('.kicad_mod'):
        filepath = os.path.join(dir_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find (model \"...step lines that don't have a closing quote
        new_content = re.sub(
            r'\(model\s+\"([^\"]+\.step)\s*\n',
            r'(model "\1"\n',
            content
        )
        new_content = re.sub(
            r'\(model\s+\"([^\"]+\.wrl)\s*\n',
            r'(model "\1"\n',
            new_content
        )
        
        if new_content != content:
            print(f'Fixed {filename}')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
print('Done.')
