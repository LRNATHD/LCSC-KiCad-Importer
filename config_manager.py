import os
import sys
import configparser

def get_base_dir():
    """Get the absolute path to the directory containing the executable or script."""
    if getattr(sys, 'frozen', False):
        # Running as a compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as a python script
        return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_base_dir(), 'config.ini')

DEFAULT_CONFIG = {
    'Settings': {
        'HOTKEY': 'ctrl+shift+d',
        'LIBRARY_DIR': r'C:\Users\Noahs\My Drive\computers\Kicad_Bits',
        'SYMBOL_LIB': 'LCSC_Imports',
        'FOOTPRINT_LIB': 'LCSC_Imports'
    }
}

def load_config():
    """Load configuration from config.ini, creating it with defaults if missing."""
    config = configparser.ConfigParser()
    
    if not os.path.exists(CONFIG_FILE):
        config.read_dict(DEFAULT_CONFIG)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write("# LCSC to KiCad Importer - Configuration File\n")
            f.write("# You can edit these settings and restart the application.\n\n")
            config.write(f)
            f.write("\n# --- Explanations ---\n")
            f.write("# hotkey: The keyboard shortcut to activate the background importer.\n")
            f.write("# library_dir: The absolute folder path where footprints, 3D models, and the EasyEDA symbol library will be saved.\n")
            f.write("# symbol_lib: The target library name to insert the symbol into (e.g., EasyEDA).\n")
            f.write("# footprint_lib: The target library name to insert the footprint into (e.g., EasyEDA).\n")
    else:
        config.read(CONFIG_FILE, encoding='utf-8')
        
        # Ensure all required keys exist
        changed = False
        if 'Settings' not in config:
            config.add_section('Settings')
            changed = True
            
        for key, default_value in DEFAULT_CONFIG['Settings'].items():
            if not config.has_option('Settings', key):
                config.set('Settings', key, default_value)
                changed = True
                
        if changed:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                config.write(f)
                
    return config['Settings']

def get_config_path():
    return CONFIG_FILE

# Load once when imported
settings = load_config()

HOTKEY = settings.get('HOTKEY')
LIBRARY_DIR = settings.get('LIBRARY_DIR')
SYMBOL_LIB = settings.get('SYMBOL_LIB')
FOOTPRINT_LIB = settings.get('FOOTPRINT_LIB')
