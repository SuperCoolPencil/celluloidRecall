import os
import json
import platform

SETTINGS_PATH = os.path.expanduser("~/.config/cue_settings.json")
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"

def get_defaults():
    if IS_WINDOWS:
        if os.path.exists(r"C:\Program Files\VideoLAN\VLC\vlc.exe"):
            return {"player_executable": r"C:\Program Files\VideoLAN\VLC\vlc.exe", "player_type": "vlc_rc"}
        return {"player_executable": "mpv", "player_type": "mpv_native"}
    elif IS_MACOS:
         return {"player_executable": "/Applications/VLC.app/Contents/MacOS/VLC", "player_type": "vlc_rc"}
    else:
        return {"player_executable": "celluloid", "player_type": "celluloid_ipc"}

def load_settings():
    defaults = get_defaults()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                saved = json.load(f)
                defaults.update(saved)
        except: pass
    return defaults

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=2)
