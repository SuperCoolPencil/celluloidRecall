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
    
    # 1. Create the basic session entry
    entry = {
        "is_folder": is_folder,
        # Use .get() for safety in case keys are missing
        "last_played_file": result_data.get('path', path),
        "last_played_position": result_data.get('position', 0),
        "total_duration": result_data.get('duration', 0),
        "last_played_timestamp": datetime.datetime.now().isoformat()
    }

    # 2. === THE FIX: Save the clean title and season info ===
    if 'clean_title' in result_data:
        entry['clean_title'] = result_data['clean_title']
    
    if 'season_number' in result_data:
        entry['season_number'] = result_data['season_number']

    sessions[path] = entry
    save_session_data(sessions)

def delete_session(path):
    sessions = load_sessions()
    if path in sessions:
        del sessions[path]
        save_session_data(sessions)