import os
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
