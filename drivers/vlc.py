import subprocess
import socket
import time
from core.utils import find_free_port

def play(executable, path, start_pos=None, playlist_idx=None, resume_file=None):
    port = find_free_port()
    cmd = [executable, "--extraintf", "rc", "--rc-host", f"localhost:{port}"]
    if start_pos: cmd.extend(["--start-time", str(start_pos)])
    cmd.append(path)

    try:
        proc = subprocess.Popen(cmd)
    except FileNotFoundError:
        return None

    last_pos, last_dur = 0, 0
    connected = False
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1.0)
    
    for _ in range(10):
        try:
            time.sleep(1)
            client.connect(('localhost', port))
            connected = True
            break
        except: continue
            
    if not connected: return None

    def query(c):
        try:
            client.sendall(f"{c}\n".encode())
            data = client.recv(1024).decode().strip().replace('>', '').strip()
            lines = data.split('\n')
            for line in lines:
                if line.isdigit(): return int(line)
            return 0
        except: return 0

    while proc.poll() is None:
        t = query("get_time")
        l = query("get_length")
        if t > 0: last_pos = t
        if l > 0: last_dur = l
        time.sleep(1)

    client.close()
    return {"path": path, "position": last_pos, "duration": last_dur}
