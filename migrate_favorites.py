import os
import re
import shutil
import tkinter as tk
from tkinter import ttk, messagebox

OLD_DIR = r'C:\Users\LRNA\Desktop\Kicad-Design-Library'
NEW_DIR = r'G:\Other computers\My Laptop\synced\Kicad_Bits\LCSC_Imports'

def parse_symbols(text):
    symbols = []
    idx = 0
    while True:
        idx = text.find('\n  (symbol "', idx)
        if idx == -1:
            # Also check if it's the very first line without newline
            if text.startswith('(symbol "'):
                idx = 0
            else:
                break
                
        name_start = idx + text[idx:].find('"') + 1
        name_end = text.find('"', name_start)
        name = text[name_start:name_end]
        
        bracket_count = 0
        end_idx = -1
        start_bracket = text.find('(', idx)
        for i in range(start_bracket, len(text)):
            if text[i] == '(':
                bracket_count += 1
            elif text[i] == ')':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx != -1:
            block = text[start_bracket:end_idx]
            
            val_match = re.search(r'\(property "Value" "([^"]+)"', block)
            val = val_match.group(1) if val_match else ""
            
            fp_match = re.search(r'\(property "Footprint" "([^:]+):([^"]+)"', block)
            fp = fp_match.group(2) if fp_match else ""
            
            symbols.append({
                'name': name,
                'value': val,
                'footprint': fp,
                'block': block
            })
            idx = end_idx
        else:
            idx += 1
    return symbols

def migrate():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "No components selected!")
        return
        
    os.makedirs(os.path.join(NEW_DIR, 'Symbols'), exist_ok=True)
    new_sym_file = os.path.join(NEW_DIR, 'Symbols', 'LCSC_Imports.kicad_sym')
    
    # Init new lib if needed
    if not os.path.exists(new_sym_file):
        with open(new_sym_file, 'w', encoding='utf-8') as f:
            f.write('(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)\n)\n')
            
    with open(new_sym_file, 'r', encoding='utf-8') as f:
        new_content = f.read()
        
    count = 0
    for item in selected:
        sym_data = symbols_dict[item]
        
        # 1. Copy symbol
        if f'(symbol "{sym_data["name"]}"' not in new_content:
            new_content = new_content.rstrip()
            if new_content.endswith(')'):
                # Format with 2 spaces indent
                indented_block = "\n  " + sym_data['block'].replace('\n', '\n  ')
                new_content = new_content[:-1] + indented_block + "\n)\n"
        
        # 2. Copy footprint & update 3D path
        fp_name = sym_data['footprint']
        if fp_name:
            # When old footprints were in EasyEDA.pretty, JLC2KiCadLib sets footprint name as EasyEDA:R0402
            # We need to strip EasyEDA: from fp_name if it exists because JLC2KiCadLib sets it
            clean_fp_name = fp_name
            if ':' in clean_fp_name:
                clean_fp_name = clean_fp_name.split(':', 1)[1]
                
            old_fp = os.path.join(OLD_DIR, 'EasyEDA.pretty', f'{clean_fp_name}.kicad_mod')
            new_fp_dir = os.path.join(NEW_DIR, 'Footprints', 'LCSC_Imports.pretty')
            new_fp = os.path.join(new_fp_dir, f'{clean_fp_name}.kicad_mod')
            
            # Since we moved the library to LCSC_Imports, we must also update the footprint reference in the symbol
            if f'"EasyEDA:{clean_fp_name}"' in new_content:
                new_content = new_content.replace(f'"EasyEDA:{clean_fp_name}"', f'"LCSC_Imports:{clean_fp_name}"')
                
            if os.path.exists(old_fp):
                os.makedirs(new_fp_dir, exist_ok=True)
                with open(old_fp, 'r', encoding='utf-8') as f:
                    fp_content = f.read()
                    
                # Rewrite absolute path to new directory
                old_unix = OLD_DIR.replace('\\', '/')
                new_unix = NEW_DIR.replace('\\', '/')
                # In the footprint, the 3d model path must point to 3D_Models/LCSC_Imports.3dshapes
                fp_content = fp_content.replace(old_unix + '/EasyEDA.3dshapes', new_unix + '/3D_Models/LCSC_Imports.3dshapes')
                
                with open(new_fp, 'w', encoding='utf-8') as f:
                    f.write(fp_content)
                    
                # 3. Copy 3D model if it exists
                # Extract 3D model paths from the footprint
                model_paths = re.findall(r'\(model "([^"]+)"', fp_content)
                for mpath in model_paths:
                    if mpath.startswith(new_unix):
                        # It's a local model
                        # rel_path was relative to NEW_DIR, but now it's 3D_Models/LCSC_Imports.3dshapes/...
                        # We extract just the filename
                        filename = mpath.split('/')[-1]
                        old_model = os.path.join(OLD_DIR, 'EasyEDA.3dshapes', filename)
                        new_model = os.path.join(NEW_DIR, '3D_Models', 'LCSC_Imports.3dshapes', filename)
                        
                        if os.path.exists(old_model):
                            os.makedirs(os.path.dirname(new_model), exist_ok=True)
                            shutil.copy2(old_model, new_model)

        count += 1
        
    # Save the updated symbol library
    with open(new_sym_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    messagebox.showinfo("Success", f"Successfully migrated {count} components to the new library!")

# --- GUI Setup ---
old_sym_file = os.path.join(OLD_DIR, 'EasyEDA.kicad_sym')
if not os.path.exists(old_sym_file):
    print("Old library not found!")
    exit()

with open(old_sym_file, 'r', encoding='utf-8') as f:
    content = f.read()
    
parsed = parse_symbols(content)
symbols_dict = {p['name']: p for p in parsed}

root = tk.Tk()
root.title("Migrate Favorite Components")
root.geometry("800x600")

lbl = tk.Label(root, text=f"Select parts to migrate to {NEW_DIR}\n(Hold CTRL or SHIFT to select multiple)", pady=10)
lbl.pack()

columns = ('Value', 'Footprint')
tree = ttk.Treeview(root, columns=columns, show='headings', selectmode='extended')
tree.heading('Value', text='Value / Part #')
tree.heading('Footprint', text='Footprint')
tree.column('Value', width=200)
tree.column('Footprint', width=200)

# We actually want the Symbol Name visible too
tree['columns'] = ('Name', 'Value', 'Footprint')
tree.heading('Name', text='Symbol Name')
tree.column('Name', width=300)

for p in parsed:
    tree.insert('', tk.END, iid=p['name'], values=(p['name'], p['value'], p['footprint']))

tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

btn = tk.Button(root, text="Migrate Selected", command=migrate, bg="green", fg="white", font=("Arial", 12, "bold"))
btn.pack(pady=20)

root.mainloop()
