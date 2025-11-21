import os
import sys
import platform
import tkinter as tk
from tkinter import filedialog
import streamlit as st

# --- Local Imports ---
try:
    from core import settings as settings_mgr
    from core import session as session_mgr
    from core.utils import format_time, get_media_files, format_remaining, get_folder_stats
    from drivers import play_media
except ImportError:
    # Mocking for demonstration if modules are missing
    st.error("Core modules missing. Please ensure 'core' and 'drivers' packages exist.")
    st.stop()

# --- Configuration ---
PAGE_TITLE = "Cue"
PAGE_ICON = "⏯️"

# --- Modern UI CSS ---
MODERN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* --- Global Resets --- */
    .stApp {
        background-color: #09090b; /* Zinc-950 */
        font-family: 'Inter', sans-serif;
    }
    header { visibility: hidden; }
    
    /* --- Typography --- */
    h1, h2, h3 { letter-spacing: -0.025em; }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    
    .sub-header {
        font-size: 0.9rem;
        color: #52525b;
        font-weight: 400;
        margin-bottom: 2rem;
        border-bottom: 1px solid #27272a;
        padding-bottom: 1rem;
    }

    /* --- Card Component --- */
    .cue-card {
        background: linear-gradient(180deg, #18181b 0%, #0e0e11 100%);
        border: 1px solid #27272a;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 0px; /* Tighten gap between card and buttons */
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
        transition: all 0.2s ease;
    }
    
    .cue-card:hover {
        border-color: #3f3f46;
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
    }

    .card-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f4f4f5;
        margin-bottom: 10px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* --- Badges --- */
    .badge-container { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
    
    .badge {
        font-size: 0.65rem;
        padding: 4px 10px;
        border-radius: 99px; /* Pill shape */
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .b-folder { background: #27272a; color: #a1a1aa; border: 1px solid #3f3f46; }
    .b-accent { background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.2); }
    .b-success { background: rgba(52, 211, 153, 0.1); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.2); }

    /* --- Stats & Progress --- */
    .stats-row {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #71717a;
        margin-top: 8px;
    }
    .time-remaining { color: #fbbf24; font-weight: 600; }

    /* --- Streamlit Overrides --- */
    /* Thin Progress Bar */
    .stProgress > div > div > div > div {
        height: 4px !important;
        border-radius: 4px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    .stProgress { margin-top: 10px; margin-bottom: 10px; }
    
    /* Buttons */
    button[kind="secondary"] {
        border: 1px solid #27272a;
        background: #18181b;
        color: #a1a1aa;
        border-radius: 8px;
        transition: all 0.2s;
    }
    button[kind="secondary"]:hover {
        border-color: #52525b;
        color: #fff;
        background: #27272a;
    }
    
    /* Input Field */
    div[data-baseweb="input"] {
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 10px;
        color: white;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0c0c0e;
        border-right: 1px solid #27272a;
    }
</style>
"""

# --- Init ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
st.markdown(MODERN_CSS, unsafe_allow_html=True)

# --- Helpers ---
def open_file_dialog(select_folder=False):
    try:
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        path = filedialog.askdirectory() if select_folder else filedialog.askopenfilename()
        root.destroy()
        return path
    except: return None

def launch_media(path, settings, start=0, idx=None, resume_f=None):
    with st.spinner(f"Opening {os.path.basename(path)}..."):
        res = play_media(settings, path, start, idx, resume_f)
        if res and res.get('position', 0) > 5:
            session_mgr.update_session(path, res, os.path.isdir(path))
            return True
    return False

# --- Components ---

def render_sidebar(settings):
    with st.sidebar:
        st.markdown("### Library")
        if st.button("📂 Open Folder", use_container_width=True):
            if p := open_file_dialog(True): st.session_state['pending_play'] = p
        if st.button("📄 Open File", use_container_width=True):
            if p := open_file_dialog(False): st.session_state['pending_play'] = p
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### System")
        
        with st.expander("⚙️ Preferences"):
            if 'w_exe' not in st.session_state: st.session_state.w_exe = settings.get('player_executable', 'mpv')
            if 'w_mode' not in st.session_state: st.session_state.w_mode = settings.get('player_type', 'mpv_native')
            
            modes = ["mpv_native", "celluloid_ipc", "vlc_rc"]
            st.radio("Driver", modes, key="w_mode")
            st.text_input("Path", key="w_exe")
            
            if st.button("Save", use_container_width=True):
                settings.update({'player_executable': st.session_state.w_exe, 'player_type': st.session_state.w_mode})
                settings_mgr.save_settings(settings)
                st.rerun()

        if st.button("🛑 Quit", type="secondary", use_container_width=True): os._exit(0)

def render_card(path, data):
    fname = os.path.basename(data.get('last_played_file', 'Unknown'))
    pos, dur = data.get('last_played_position', 0), data.get('total_duration', 0)
    is_folder = data.get('is_folder', False)
    
    # Logic
    ratio = min(pos/dur, 1.0) if dur else 0
    is_done = ratio > 0.95
    remaining = dur - pos
    
    # Badges HTML
    badges = []
    icon = "📄"
    
    if is_folder:
        icon = "📂"
        stats = get_folder_stats(path, data['last_played_file'])
        if stats:
            curr, total = stats
            pct = int(((curr if is_done else curr-1)/total)*100)
            badges.append(f'<span class="badge b-folder">Series {pct}%</span>')
            badges.append(f'<span class="badge b-accent">Ep {curr}/{total}</span>')
    else:
        badges.append(f'<span class="badge b-folder">Media File</span>')

    if is_done: badges.append('<span class="badge b-success">Completed</span>')
    
    html = f"""
    <div class="cue-card">
        <div class="card-title">{icon} {fname}</div>
        <div class="badge-container">{"".join(badges)}</div>
        <div class="stats-row">
            <span>{format_time(pos)} / {format_time(dur)}</span>
            <span class="time-remaining">{'Finished' if is_done else format_remaining(remaining, is_folder)}</span>
        </div>
    </div>
    """
    
    # Render
    st.markdown(html, unsafe_allow_html=True)
    
    # Progress Bar (Outside HTML for Streamlit native rendering)
    if not is_done:
        st.progress(ratio)
    else:
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # Actions
    c1, c2 = st.columns([0.85, 0.15])
    with c1:
        lbl = "↺ Replay" if is_done else "▶ Resume"
        if st.button(lbl, key=f"p_{path}", use_container_width=True):
            st.session_state['resume_data'] = (path, is_done, pos, is_folder, data['last_played_file'])
            st.rerun()
    with c2:
        if st.button("✕", key=f"d_{path}", help="Remove"):
            session_mgr.delete_session(path)
            st.rerun()
            
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# --- Main Loop ---
def main():
    settings = settings_mgr.load_settings()
    
    # Logic Handlers
    if 'pending_play' in st.session_state:
        if launch_media(st.session_state.pop('pending_play'), settings): st.rerun()
        
    if 'resume_data' in st.session_state:
        path, done, pos, is_dir, last_f = st.session_state.pop('resume_data')
        if os.path.exists(path):
            idx, res_f = None, None
            if is_dir:
                files = get_media_files(path)
                if last_f in files: idx, res_f = files.index(last_f), last_f
            if launch_media(path, settings, 0 if done else pos, idx, res_f): st.rerun()

    # UI Render
    render_sidebar(settings)
    
    st.markdown('<div class="main-header">Cue.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Playback History • {len(session_mgr.load_sessions())} items</div>', unsafe_allow_html=True)

    # Search
    sessions = session_mgr.load_sessions()
    query = st.text_input("Search", placeholder="Filter...", label_visibility="collapsed")
    
    items = sorted(
        [i for i in sessions.items() if query.lower() in i[0].lower() or query.lower() in i[1].get('last_played_file','').lower()],
        key=lambda x: x[1].get('last_played_timestamp', ''), reverse=True
    )

    if not items:
        st.info("Library is empty. Open a file to start watching.")
    else:
        for path, data in items:
            render_card(path, data)

if __name__ == "__main__":
    main()