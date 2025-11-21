import os
import datetime
import socket
from contextlib import closing

def format_time(seconds):
    if not seconds: return "0:00:00"
    return str(datetime.timedelta(seconds=int(seconds)))

def get_media_files(folder):
    exts = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.mp3', '.wav', '.ogg')
    try:
        return sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)])
    except: return []

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
