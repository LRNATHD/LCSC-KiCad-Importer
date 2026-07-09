import os
import re

lib_dir = 'C:/Users/LRNA/Desktop/Kicad-Design-Library'
kicad_3d_dir = r'C:\Program Files\KiCad\10.0\share\kicad\3dmodels'

# Regex to find 3D model paths in footprints
model_regex = re.compile(r'\(model\s+"?(\$\{KICAD10_3DMODEL_DIR\}/[^"]+)"?')

def find_replacement_model(missing_path):
    # E.g. ${KICAD10_3DMODEL_DIR}/TerminalBlock_4Ucon.3dshapes/TerminalBlock_4Ucon_1x02_P3.50mm_Horizontal.wrl
    base_name = os.path.basename(missing_path)
    
    # Extract key parameters from the filename to search for a replacement
    # e.g. "1x02_P3.50mm_Horizontal"
    match = re.search(r'(1x\d\d_P\d+\.\d+mm_Horizontal|1x\d\d_P\d+\.\d+mm_Vertical)', base_name)
    if not match:
        return None
        
    search_param = match.group(1)
    
    # We'll search in all 3dshapes directories in KiCad
    if not os.path.exists(kicad_3d_dir):
        return None
        
    for root, dirs, files in os.walk(kicad_3d_dir):
        # Only check .step files
        for f in files:
            if f.endswith('.step') and search_param in f:
                # Found a replacement!
                # E.g. TerminalBlock_Phoenix.3dshapes/PhoenixContact_MCV_1,5_2-G-3.5_1x02_P3.50mm_Vertical.step
                rel_dir = os.path.basename(root)
                return f"${{KICAD10_3DMODEL_DIR}}/{rel_dir}/{f}"
                
    return None

count_fixed = 0
count_broken = 0

for root, _, files in os.walk(lib_dir):
    for f in files:
        if f.endswith('.kicad_mod'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            orig = content
            
            # Find all models
            def replacer(match):
                global count_fixed, count_broken
                full_match = match.group(0)
                model_path = match.group(1)
                
                # Check if it exists
                actual_path = model_path.replace('${KICAD10_3DMODEL_DIR}', kicad_3d_dir).replace('/', '\\')
                if not os.path.exists(actual_path):
                    replacement = find_replacement_model(model_path)
                    if replacement:
                        print(f"Fixed {f}: {os.path.basename(model_path)} -> {os.path.basename(replacement)}")
                        count_fixed += 1
                        return full_match.replace(model_path, replacement)
                    else:
                        print(f"WARNING: Could not find replacement for {f}: {model_path}")
                        count_broken += 1
                return full_match
                
            content = model_regex.sub(replacer, content)
            
            if content != orig:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)

print(f'Done. Fixed {count_fixed} footprints. Unfixable: {count_broken}')
