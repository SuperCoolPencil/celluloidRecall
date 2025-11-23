import os
import math
from typing import List

def get_media_files(path: str) -> List[str]:
    """
    Returns a sorted list of media files in a given directory.
    """
    media_files = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith(('.mkv', '.mp4', '.avi', '.mov')):
                    media_files.append(os.path.join(root, file))
    return sorted(media_files)

def format_seconds_to_human_readable(seconds: float) -> str:
    """
    Converts a float of seconds into a human-readable string (e.g., "1h 25m 30s").
    Handles hours, minutes, and seconds, omitting units if their value is zero.
    """
    if seconds is None:
        return "N/A"
    
    seconds = math.ceil(seconds) # Round up to the nearest whole second
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if remaining_seconds > 0 or (hours == 0 and minutes == 0 and minutes == 0): # Always show seconds if total time is less than a minute
        parts.append(f"{int(remaining_seconds)}s")

    return " ".join(parts)
