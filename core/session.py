import os
import json
import datetime
import uuid
from core.settings import load_config_paths

_, CONFIG_SESSIONS_PATH = load_config_paths()

CACHE_PATH = CONFIG_SESSIONS_PATH

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
    
    # Get existing session or create a new one
    session = sessions.get(path, {})

    # If it's a new session, assign a UUID and other initial details
    if 'id' not in session:
        session['id'] = str(uuid.uuid4())
        session['is_folder'] = is_folder
        if 'season_number' in result_data:
            session['season_number'] = result_data['season_number']
        # Set clean_title from guessit only for new sessions
        if 'clean_title' in result_data:
            session['clean_title'] = result_data['clean_title']

    # Update details that change on every run
    session["last_played_file"] = result_data.get('path', path)
    session["last_played_position"] = result_data.get('position', 0)
    session["total_duration"] = result_data.get('duration', 0)
    session["last_played_timestamp"] = datetime.datetime.now().isoformat()

    sessions[path] = session
    save_session_data(sessions)

def update_session_metadata(path, key, value):
    sessions = load_sessions()
    if path in sessions:
        sessions[path][key] = value
        save_session_data(sessions)

def delete_session(path):
    sessions = load_sessions()
    if path in sessions:
        del sessions[path]
        save_session_data(sessions)
