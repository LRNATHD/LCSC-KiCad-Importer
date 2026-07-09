import os
import re

lib_dir = 'C:/Users/LRNA/Desktop/Kicad-Design-Library'
easyeda_3d_dir = os.path.join(lib_dir, 'EasyEDA.3dshapes').replace('\\', '/')
footprint_3d_dir = os.path.join(lib_dir, 'Footprint.3dshapes').replace('\\', '/')

count = 0
for root, _, files in os.walk(lib_dir):
    for f in files:
        if f.endswith('.kicad_mod'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            orig = content
            
            # Use regex to replace both quoted and unquoted model paths
            content = re.sub(r'\(model\s+["\']?\.\./EasyEDA\.3dshapes/', f'(model "{easyeda_3d_dir}/', content)
            content = re.sub(r'\(model\s+["\']?\.\./Footprint\.3dshapes/', f'(model "{footprint_3d_dir}/', content)
            
            # We already fixed the KISYS3DMOD ones in the last run, but do it again safely
            content = content.replace('${KISYS3DMOD}', '${KICAD10_3DMODEL_DIR}')
            
            if content != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f'Fixed: {path}')
                count += 1

print(f'Done. Fixed {count} footprints.')
