import pystray
from PIL import Image
import os
import sys
import threading
from config_manager import get_config_path

def create_image(width, height):
    # Fallback image if icon.png is missing
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    return image

def setup_startup(enable=True):
    import winshell
    from win32com.client import Dispatch
    
    startup_folder = winshell.startup()
    path = os.path.join(startup_folder, "LCSC_KiCad_Importer.lnk")
    
    if enable:
        if getattr(sys, 'frozen', False):
            target = sys.executable
        else:
            # When running as script, link to pythonw.exe main.py
            target = sys.executable
            
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        
        if not getattr(sys, 'frozen', False):
            shortcut.Arguments = os.path.abspath("main.py")
            
        shortcut.WorkingDirectory = os.path.dirname(target) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))
        shortcut.IconLocation = target
        shortcut.save()
    else:
        if os.path.exists(path):
            os.remove(path)

def check_startup():
    import winshell
    startup_folder = winshell.startup()
    path = os.path.join(startup_folder, "LCSC_KiCad_Importer.lnk")
    return os.path.exists(path)

def toggle_startup(icon, item):
    is_enabled = check_startup()
    setup_startup(not is_enabled)

def open_config(icon, item):
    os.startfile(get_config_path())

def on_quit(icon, item):
    icon.stop()
    os._exit(0)

global_icon = None

def show_notification(message, title="LCSC Importer"):
    if global_icon:
        try:
            global_icon.notify(message, title)
        except Exception as e:
            print(f"Notification error: {e}")

def start_tray_icon():
    global global_icon
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
            
        icon_path = os.path.join(base_path, 'icon.png')
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = create_image(64, 64)
    except Exception:
        image = create_image(64, 64)

    menu = pystray.Menu(
        pystray.MenuItem("Start with Windows", toggle_startup, checked=lambda item: check_startup()),
        pystray.MenuItem("Open Config", open_config),
        pystray.MenuItem("Quit", on_quit)
    )

    global_icon = pystray.Icon("lcsc_importer", image, "LCSC to KiCad Importer", menu)
    global_icon.run()
