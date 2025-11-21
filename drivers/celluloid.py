import subprocess
import socket
import json
import time
import uuid
import os

def send_ipc_command(sock_path, command):
    if not os.path.exists(sock_path): return None
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.5)
        client.connect(sock_path)
        message = json.dumps(command) + "\n"
        client.sendall(message.encode('utf-8'))
        response = client.recv(4096)
        client.close()
        response_str = response.decode('utf-8').strip()
        for line in response_str.split('\n'):
            try:
                j = json.loads(line)
                if 'data' in j or 'error' in j: return j
            except: continue
        return None
    except: return None

def get_status(sock_path):
    pos_resp = send_ipc_command(sock_path, {"command": ["get_property", "time-pos"]})
    dur_resp = send_ipc_command(sock_path, {"command": ["get_property", "duration"]})
    path_resp = send_ipc_command(sock_path, {"command": ["get_property", "path"]})
    
    pos = pos_resp.get('data') if pos_resp else None
    dur = dur_resp.get('data') if dur_resp else None
    fpath = path_resp.get('data') if path_resp else None
    return fpath, pos, dur

def play(executable, path, start_pos=None, playlist_idx=None, resume_file=None):
    if os.name == 'nt': return None # Windows not supported for this driver

    socket_path = f"/tmp/cue_ipc_{uuid.uuid4().hex}.sock"
    cmd = [executable]
    cmd.append(f"--mpv-input-ipc-server={socket_path}")
    if start_pos: cmd.append(f"--mpv-start={start_pos}")
    if playlist_idx is not None: cmd.append(f"--mpv-playlist-start={playlist_idx}")
    cmd.append(path)

    try:
        proc = subprocess.Popen(cmd)
    except FileNotFoundError:
        return None

    last_pos, last_dur, last_path = 0, 0, None
    time.sleep(2.0)

    while proc.poll() is None:
        fpath, pos, dur = get_status(socket_path)
        if pos: last_pos = pos
        if dur: last_dur = dur
        if fpath: last_path = fpath
        time.sleep(1)

    if os.path.exists(socket_path): os.remove(socket_path)

    final_path = last_path if last_path else path
    if os.path.isdir(path) and last_path:
        full = os.path.join(path, last_path)
        if os.path.exists(full): final_path = full
    
    return {"path": final_path, "position": last_pos, "duration": last_dur}
