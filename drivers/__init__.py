from . import mpv, celluloid, vlc

def play_media(settings, path, start_pos=None, playlist_idx=None, resume_file=None):
    exe = settings['player_executable']
    mode = settings['player_type']
    
    if mode == "mpv_native":
        return mpv.play(exe, path, start_pos, playlist_idx, resume_file)
    elif mode == "celluloid_ipc":
        return celluloid.play(exe, path, start_pos, playlist_idx, resume_file)
    elif mode == "vlc_rc":
        return vlc.play(exe, path, start_pos, playlist_idx, resume_file)
    return None
