import subprocess
import socket
import time
import os
import streamlit as st
from core.utils import find_free_port

def play(executable, path, start_pos=None, playlist_idx=None, resume_file=None):
    # Sanity Check for correct executable
    exe_name = os.path.basename(executable).lower()
    if "mpv" in exe_name or "celluloid" in exe_name:
        st.error(f"⚠️ Configuration Error: You selected the VLC driver, but your Player Path is set to `{executable}`.")
        return None

    port = find_free_port()
    
    # --extraintf=rc enables the Remote Control interface
    # --rc-host binds it to a local port we can talk to
    cmd = [
        executable,
        "--extraintf=rc", 
        f"--rc-host=localhost:{port}",
        "--one-instance",
        "--no-playlist-enqueue"
    ]
    
    if start_pos:
        cmd.append(f"--start-time={start_pos}")
        
    cmd.append(path)

    try:
        proc = subprocess.Popen(cmd)
    except FileNotFoundError:
        st.error(f"❌ Executable not found: `{executable}`")
        return None

    # --- Socket Connection ---
    last_pos, last_dur = 0, 0
    connected = False
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1.0) # 1 second timeout
    
    for i in range(10):
        try:
            time.sleep(0.5)
            client.connect(('localhost', port))
            connected = True
            break
        except:
            continue
            
    if not connected:
        st.warning("Could not connect to VLC interface.")
        return None

    # --- HELPER: Read until prompt ---
    def read_response():
        """Reads data from socket until the VLC prompt '>' is seen."""
        data = ""
        try:
            while ">" not in data:
                chunk = client.recv(4096).decode('utf-8', errors='ignore')
                if not chunk: break # Socket closed
                data += chunk
        except socket.timeout:
            pass
        return data

    # 1. Clear the initial Welcome Message banner so it doesn't clog our buffer
    read_response()

    # 2. Query Function
    def query(cmd_str):
        try:
            # Send command
            client.sendall(f"{cmd_str}\n".encode())
            
            # Read exact response
            raw_response = read_response()
            
            # Clean up response (remove the '>' prompt and whitespace)
            clean_lines = raw_response.replace('>', '').split('\n')
            
            # Find the first line that is a pure number
            for line in clean_lines:
                line = line.strip()
                if line.isdigit():
                    return int(line)
            return 0
        except Exception:
            return 0

    # --- Polling Loop ---
    while proc.poll() is None:
        # We query time and length sequentially
        t = query("get_time")
        l = query("get_length")
        
        if t > 0: last_pos = t
        if l > 0: last_dur = l
        
        time.sleep(1)

    try:
        client.close()
    except: pass

    return {"path": path, "position": last_pos, "duration": last_dur}