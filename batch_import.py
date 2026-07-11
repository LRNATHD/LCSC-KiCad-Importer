import csv
import sys
import re
from part_downloader import download_part
import config_manager

sys.stdout.reconfigure(encoding='utf-8')

# Override target libraries for the batch run
config_manager.SYMBOL_LIB = "Legacy_Parts"
config_manager.FOOTPRINT_LIB = "Legacy_Parts"

def is_standard_passive(category, description):
    # Check if category is a standard SMD package (0201, 0402, 0603, 0805, 1206, 1210, 2010, 2512)
    standard_packages = ['0201', '0402', '0603', '0805', '1206', '1210', '2010', '2512']
    category = str(category).strip()
    
    is_standard_pkg = category in standard_packages
    
    desc_lower = str(description).lower()
    is_rcl = 'resistor' in desc_lower or 'capacitor' in desc_lower or 'inductor' in desc_lower
    
    return is_standard_pkg and is_rcl

def main():
    parts_to_download = []
    skipped_passives = []
    skipped_digikey = []

    print("[i] Parsing Consolidated_Parts.csv...")
    with open('Consolidated_Parts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dist = row.get('Distributor', '').strip()
            part_no = row.get('Distributor Part Number', '').strip()
            desc = row.get('Description', '').strip()
            category = row.get('Category/Package', '').strip()
            
            if dist.lower() == 'digikey':
                skipped_digikey.append(row)
                continue
                
            if dist.lower() == 'lcsc':
                if is_standard_passive(category, desc):
                    skipped_passives.append(row)
                else:
                    parts_to_download.append(row)

    print(f"\n[i] Skipped {len(skipped_digikey)} DigiKey parts (Auto-search not reliable without exact LCSC number).")
    print(f"[i] Skipped {len(skipped_passives)} standard passives.")
    print(f"[i] Found {len(parts_to_download)} LCSC parts to download.")

    if '--dry-run' in sys.argv:
        print("\n[DRY RUN] Parts to be downloaded:")
        for p in parts_to_download:
            print(f"  - {p['Distributor Part Number']} ({p['Description']})")
        return

    success_count = 0
    fail_count = 0

    for i, p in enumerate(parts_to_download):
        lcsc_no = p['Distributor Part Number']
        print(f"\n--- [{i+1}/{len(parts_to_download)}] Downloading {lcsc_no} ---")
        try:
            success, sym_name, sym_block, attrs = download_part(lcsc_no)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"[-] Unhandled error downloading {lcsc_no}: {e}")
            fail_count += 1

    print("\n==============================")
    print("BATCH IMPORT COMPLETE")
    print(f"Successful: {success_count}")
    print(f"Failed:     {fail_count}")
    print("==============================")

if __name__ == '__main__':
    main()
