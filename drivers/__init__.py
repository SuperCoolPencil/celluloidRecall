from typing import Dict, Any, Optional
from core.domain import PlaybackState
from core import settings as settings_mgr
from core.drivers.mpv_driver import MpvDriver
from core.drivers.vlc_driver import VlcDriver

# Mapping of player types to their respective driver classes
PLAYER_DRIVERS_MAP = {
    "mpv_native": MpvDriver,
    "vlc_rc": VlcDriver,
    # "celluloid_ipc": CelluloidDriver, # If implemented
}

def play_media(app_settings: Dict[str, Any], path: str, start_pos: float = 0.0, 
               playlist_idx: Optional[int] = None, resume_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Plays a media file using the player driver specified in app_settings.
    This function acts as a bridge from the old main.py's `play_media` call
    to the new IPlayerDriver interface.
    
    Args:
        app_settings (Dict[str, Any]): Application settings containing player_type and player_executable.
        path (str): The main path to the media file or folder.
        start_pos (float): The time in seconds to start playback from.
        playlist_idx (Optional[int]): Not directly used by the facade, but kept for compatibility.
        resume_file (Optional[str]): The actual file to play if `path` is a folder.
                                     This will be passed to the driver.
                                     
    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the playback result,
                                  mimicking the old format.
                                  Returns None if playback fails.
    """
    player_type = app_settings.get("player_type", "mpv_native")
    # player_executable = app_settings.get("player_executable", "mpv") # Not directly used by driver classes here

    DriverClass = PLAYER_DRIVERS_MAP.get(player_type)

    if not DriverClass:
        print(f"Error: Unknown player type '{player_type}'. Falling back to MPV.")
        DriverClass = MpvDriver

    driver = DriverClass()
    
    # The `resume_file` is the actual file to be played by the driver.
    # If path is a folder, `resume_file` would be the specific episode.
    file_to_play = resume_file if resume_file else path

    try:
        playback_state: PlaybackState = driver.launch(file_to_play, start_pos)
        
        # Convert PlaybackState back to the dictionary format expected by main.py's `launch_media`
        # This is crucial for the facade to work without changing main.py extensively.
        result_dict = {
            "last_played_file": playback_state.last_played_file,
            "position": playback_state.position,
            "duration": playback_state.duration,
            "is_finished": playback_state.is_finished,
            "timestamp": playback_state.timestamp # datetime object might need to be isoformat() later in main.py
        }
        return result_dict
    except Exception as e:
        print(f"Error launching media with {player_type} driver: {e}")
        return None

# __all__ = ["play_media"] # Not strictly needed for a single function but good practice
