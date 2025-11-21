import os
import json
import datetime

CACHE_PATH = os.path.expanduser("~/.cache/cue_media_sessions.json")

def load_sessions():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def save_session_data(sessions):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, 'w') as f:
        json.dump(sessions, f, indent=2)

def update_session(path, result_data, is_folder=False):
    sessions = load_sessions()
    sessions[path] = {
        "is_folder": is_folder,
        "last_played_file": result_data['path'],
        "last_played_position": result_data['position'],
        "total_duration": result_data['duration'],
        "last_played_timestamp": datetime.datetime.now().isoformat()
    }
    save_session_data(sessions)

def delete_session(path):
    sessions = load_sessions()
    if path in sessions:
        del sessions[path]
        save_session_data(sessions)
