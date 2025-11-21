import os
import time
import datetime
import platform
import streamlit as st
import tkinter as tk
from tkinter import filedialog

# Import Modules
from core import settings as settings_mgr
from core import session as session_mgr
from core.utils import format_time, get_media_files, format_remaining, get_folder_stats
from drivers import play_media

# --- UI Configuration & Custom CSS ---
st.set_page_config(page_title="Cue", page_icon="⏯️", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    .stApp { background-color: #0E1117; }
    h1, h2, h3, p, div { font-family: 'Inter', sans-serif; }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle { color: #64748B; margin-bottom: 2rem; }

    /* Card Styling */
    .cue-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .filename {
        font-size: 1.1rem;
        font-weight: 600;
        color: #F8FAFC;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 8px;
    }

    /* Badge Row */
    .meta-row {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-bottom: 12px;
        flex-wrap: wrap;
    }
    
    .badge {
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .bg-folder { background: #334155; color: #94A3B8; }
    .bg-blue   { background: #0ea5e9; color: #e0f2fe; }
    .bg-green  { background: #10b981; color: #d1fae5; }
    .bg-purple { background: #8b5cf6; color: #ede9fe; }

    /* Stats Row */
    .stats-row {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 12px;
    }
    
    .highlight-amber { color: #f59e0b; font-weight: 600; }

    /* Progress Bar Override */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #f59e0b, #ef4444);
    }
</style>
""", unsafe_allow_html=True)

# --- Logic ---
current_settings = settings_mgr.load_settings()
if 'selected_path' not in st.session_state: st.session_state['selected_path'] = None

def update_path_based_on_mode():
    new_mode = st.session_state.widget_mode
    is_win = platform.system() == "Windows"
    is_mac = platform.system() == "Darwin"
    new_path = "mpv"
    if new_mode == "vlc_rc":
        if is_win: new_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        elif is_mac: new_path = "/Applications/VLC.app/Contents/MacOS/VLC"
        else: new_path = "vlc"
    elif new_mode == "mpv_native":
        new_path = "mpv"
    elif new_mode == "celluloid_ipc":
        new_path = "celluloid"
    st.session_state.widget_exe = new_path

def handle_play(path, start_pos=0, idx=None, resume_f=None):
    with st.spinner("Launching..."):
        res = play_media(current_settings, path, start_pos, idx, resume_f)
        if res and res.get('position', 0) > 5:
            session_mgr.update_session(path, res, is_folder=os.path.isdir(path))
            return True
        elif not res:
            st.error("Player failed to launch.")
    return False

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⏯️ Controls")
    if st.button("📂 Open Folder", use_container_width=True):
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askdirectory()
        root.destroy()
        if p: st.session_state['selected_path'] = p
    if st.button("📄 Open File", use_container_width=True):
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askopenfilename()
        root.destroy()
        if p: st.session_state['selected_path'] = p
    
    st.markdown("---")
    with st.expander("⚙️ Settings"):
        if 'widget_exe' not in st.session_state: st.session_state.widget_exe = current_settings['player_executable']
        if 'widget_mode' not in st.session_state: st.session_state.widget_mode = current_settings['player_type']
        
        options = ["mpv_native", "celluloid_ipc", "vlc_rc"]
        idx = options.index(st.session_state.widget_mode) if st.session_state.widget_mode in options else 0
        st.radio("Driver", options, index=idx, key="widget_mode", on_change=update_path_based_on_mode)
        st.text_input("Exe Path", key="widget_exe")
        if st.button("Save", use_container_width=True):
            current_settings['player_executable'] = st.session_state.widget_exe
            current_settings['player_type'] = st.session_state.widget_mode
            settings_mgr.save_settings(current_settings)
            st.rerun()

    if st.button("🛑 Exit", type="secondary", use_container_width=True): os._exit(0)

# --- Main UI ---
st.markdown('<div class="main-title">Cue</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Using driver: <b>{current_settings["player_type"]}</b></div>', unsafe_allow_html=True)

if st.session_state['selected_path']:
    path = st.session_state['selected_path']
    st.session_state['selected_path'] = None 
    if handle_play(path): st.rerun()

# Render Queue
sessions = session_mgr.load_sessions()
col_search, _ = st.columns([1, 0.1])
search = col_search.text_input("Search", placeholder="Filter history...", label_visibility="collapsed")

filtered = {k:v for k,v in sessions.items() if search.lower() in k.lower() or search.lower() in v.get('last_played_file','').lower()}
sorted_sess = sorted(filtered.items(), key=lambda i: i[1].get('last_played_timestamp',''), reverse=True)

if not sorted_sess:
    st.info("Nothing watched yet.")
else:
    for orig_path, data in sorted_sess:
        fname = os.path.basename(data['last_played_file'])
        pos = data.get('last_played_position', 0)
        dur = data.get('total_duration', 0)
        is_folder = data.get('is_folder', False)
        ts_date = data.get('last_played_timestamp', '')[:10]

        # Stats Logic
        prog_ep = min(pos/dur, 1.0) if dur else 0
        finished = prog_ep > 0.95
        remaining_sec = dur - pos
        
        # Badge Logic
        badges = []
        
        if is_folder:
            ep_stats = get_folder_stats(orig_path, data['last_played_file'])
            if ep_stats:
                curr_ep, total_eps = ep_stats
                # Calculate Series Progress based on Episodes
                # If current episode is finished, we count it as done, otherwise -1
                completed_eps = curr_ep if finished else (curr_ep - 1)
                series_pct = int((completed_eps / total_eps) * 100)
                
                badges.append(f'<span class="badge bg-folder">SERIES {series_pct}%</span>')
                badges.append(f'<span class="badge bg-blue">EP {curr_ep}/{total_eps}</span>')
        else:
            badges.append(f'<span class="badge bg-folder">FILE</span>')

        if finished:
            badges.append('<span class="badge bg-green">COMPLETED</span>')
            time_text = "Finished"
        else:
            time_text = format_remaining(remaining_sec, folder=is_folder)

        badges_html = "".join(badges)

        # Render Card
        html_card = f"""
<div class="cue-card">
<div class="filename" title="{fname}">{fname}</div>
<div class="meta-row">
{badges_html}
<span style="color:#64748B; font-size:0.75rem; margin-left:auto;">{ts_date}</span>
</div>
<div class="stats-row">
<span>{format_time(pos)} / {format_time(dur)}</span>
<span class="highlight-amber">{time_text}</span>
</div>
</div>
"""
        with st.container():
            st.markdown(html_card, unsafe_allow_html=True)
            
            if not finished:
                st.progress(prog_ep)
            
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                lbl = "🔄 Replay" if finished else "▶️ Resume"
                if st.button(lbl, key=f"p_{orig_path}", use_container_width=True):
                    if not os.path.exists(orig_path):
                        st.error("Not found.")
                    else:
                        idx, res_f = None, None
                        if is_folder:
                            files = get_media_files(orig_path)
                            last = data['last_played_file']
                            if last in files: idx = files.index(last); res_f = last
                        
                        if handle_play(orig_path, 0 if finished else pos, idx, res_f):
                            st.rerun()
            with c2:
                if st.button("✕", key=f"d_{orig_path}", help="Remove"):
                    session_mgr.delete_session(orig_path)
                    st.rerun()