import subprocess
import re
import os
import platform

def play(executable, path, start_pos=None, playlist_idx=None, resume_file=None):
    cmd = [
        executable,
        "--force-window",
        "--term-status-msg=[Cue]PATH:${path}#POS:${playback-time}#DUR:${duration}"
    ]
    
    script_path = None
    if resume_file and playlist_idx is not None and os.path.isdir(path):
        cmd.append(f"--playlist-start={playlist_idx}")
        script_content = f'''
local sought = false
local target_time = {max(start_pos-2, 0)}
function on_file_loaded()
    if not sought then
        sought = true
        mp.commandv("seek", target_time, "absolute")
    end
end
mp.register_event("file-loaded", on_file_loaded)
'''
        import tempfile
        fd, script_path = tempfile.mkstemp(suffix=".lua")
        os.close(fd)
        with open(script_path, 'w') as f: f.write(script_content)
        cmd.append(f"--script={script_path}")
    elif start_pos:
         cmd.append(f"--start={start_pos}")

    cmd.append(path)

    try:
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        proc = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            startupinfo=startupinfo
        )
    except FileNotFoundError:
        return None
    finally:
        if script_path and os.path.exists(script_path): os.remove(script_path)

    last_line = ""
    if proc.stdout:
        for line in proc.stdout.split('\n'):
            if "[Cue]" in line: last_line = line

    if not last_line: return None

    match = re.search(r"PATH:(.*?)#POS:([\d:.]+)#DUR:([\d:.]+)", last_line)
    if match:
        p_str, d_str = match.group(2), match.group(3)
        def parse_time(t):
            if ':' in str(t):
                parts = t.split(':')
                if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                elif len(parts) == 2: return float(parts[0])*60 + float(parts[1])
            return float(t) if t != "unknown" else 0
        return {"path": match.group(1), "position": parse_time(p_str), "duration": parse_time(d_str)}
    return None
