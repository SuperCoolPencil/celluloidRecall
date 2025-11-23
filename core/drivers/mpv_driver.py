import subprocess
import socket
import json
import os
import time
import sys
from typing import Optional, List
from datetime import datetime

# Assuming these imports exist in your project structure
from core.interfaces import IPlayerDriver
from core.domain import PlaybackState

class MpvDriver(IPlayerDriver):
    def __init__(self):
        self.request_id_counter = 0

    def launch(self, playlist: List[str], start_index: int = 0, start_time: float = 0.0) -> PlaybackState:
        if not playlist:
            return PlaybackState()

        # 1. Setup a unique socket name (prevents collisions if multiple players run)
        is_windows = sys.platform.startswith('win')
        socket_path = r'\\.\pipe\mpv_socket' if is_windows else f"/tmp/mpv-socket-{os.getpid()}"

        if not is_windows and os.path.exists(socket_path):
            os.remove(socket_path)

        command = [
            "mpv",
            "--no-terminal",
            f"--input-ipc-server={socket_path}",
            f"--start={start_time}",
            f"--playlist-start={start_index}",
            "--force-media-title=dummy",
            "--idle=no", # Ensure MPV closes when file ends
        ]
        command.extend(playlist)

        print(f"Launching MPV: {' '.join(command)}")
        
        process = subprocess.Popen(command)
        
        final_position = start_time
        total_duration = 0.0
        is_finished = False
        last_played_file = playlist[start_index]

        try:
            # 2. Connect to the MPV socket
            ipc = self._connect_ipc(socket_path, is_windows, timeout=5)
            if not ipc:
                raise ConnectionError("Failed to connect to MPV IPC socket.")
            
            # 3. Loop while process is alive to track progress
            while process.poll() is None:
                try:
                    # Query time-pos
                    pos = self._send_ipc_command(ipc, ["get_property", "time-pos"])
                    if pos is not None:
                        try:
                            final_position = float(pos)
                        except (ValueError, TypeError):
                            print(f"Warning: Could not convert position '{pos}' to float.")
                    
                    # Query duration (only need to do this until we get a value)
                    if total_duration == 0.0:
                        dur = self._send_ipc_command(ipc, ["get_property", "duration"])
                        if dur is not None:
                            try:
                                total_duration = float(dur)
                            except (ValueError, TypeError):
                                print(f"Warning: Could not convert duration '{dur}' to float.")
                    
                    # Get the current playing file
                    path = self._send_ipc_command(ipc, ["get_property", "path"])
                    if path:
                        last_played_file = path

                    # Don't spam the socket; check every 1 second
                    time.sleep(1)
                    
                except (BrokenPipeError, ConnectionResetError):
                    # MPV closed abruptly
                    break
            
            # 4. Cleanup
            if ipc:
                ipc.close()

            # Determine if finished (heuristic: within 5s of end)
            if total_duration > 0 and (total_duration - final_position) < 5.0:
                is_finished = True

        except Exception as e:
            print(f"IPC Error: {e}")
        finally:
            # Ensure process is dead
            if process.poll() is None:
                process.terminate()
            
            # Cleanup socket file (Linux/Mac only)
            if not is_windows and os.path.exists(socket_path):
                os.remove(socket_path)

        return PlaybackState(
            last_played_file=last_played_file,
            position=final_position,
            duration=total_duration,
            is_finished=is_finished,
            timestamp=datetime.now()
        )

    def _connect_ipc(self, path, is_windows, timeout=5):
        """Connects to the MPV IPC socket/pipe with a retry mechanism."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if is_windows:
                    # This is a simplified placeholder. Production Windows support is more complex.
                    pass
                else:
                    if os.path.exists(path):
                        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        s.connect(path)
                        return s
            except (ConnectionRefusedError, FileNotFoundError):
                time.sleep(0.1) # Wait a bit before retrying
            except Exception as e:
                print(f"Could not connect to IPC: {e}")
                return None
        print(f"IPC connection timed out after {timeout} seconds.")
        return None

    def _send_ipc_command(self, sock, command_list):
        """Sends a JSON command to MPV and waits for the specific response."""
        if not sock: return None
        
        self.request_id_counter += 1
        request_id = self.request_id_counter
        
        message = json.dumps({"command": command_list, "request_id": request_id}) + "\n"
        try:
            sock.sendall(message.encode('utf-8'))
            
            buffer = ""
            sock.settimeout(2.0)
            
            while True:
                try:
                    chunk = sock.recv(4096).decode('utf-8')
                    if not chunk: return None
                    buffer += chunk
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if not line: continue
                        try:
                            resp = json.loads(line)
                            if resp.get("request_id") == request_id:
                                return resp.get("data") if resp.get("error") == "success" else None
                        except json.JSONDecodeError:
                            pass
                except socket.timeout:
                    return None
        except Exception as e:
            print(f"Error sending IPC command or reading response: {e}")
            return None
        return None
