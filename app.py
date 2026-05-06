import requests
import streamlit as st
import json
import os

# --- CONFIG ---
st.set_page_config(page_title="Bio-Stack | Wild West", page_icon="🌿", layout="wide")

# --- CLAUDE'S TROPICAL CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0f1a0e;
        color: #d4c9a8;
        font-family: 'Georgia', serif;
    }}
    .species-card {{
        background: #131d12;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2a3a28;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .sci-name {{ color: #c8d8a8; font-style: italic; font-size: 1.2rem; font-weight: bold; }}
    .local-name {{ color: #7a9a6a; font-size: 0.9rem; }}
    .status-badge {{
        padding: 2px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        background: #1e2e1c;
        color: #a8c878;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- UTILITIES ---
def load_db():
    if os.path.exists("data/species_db.json"):
        with open("data/species_db.json", "r") as f:
            return json.load(f)
    return []

db = load_db()

# --- HEADER ---
st.title("🌿 BIO-STACK")
st.caption("Wild West Sandbox · Taxonomy Engine v1.0")

search = st.text_input("🔍 Search specimen by name, habitat, or Mandarin...", "")

# --- CARD RENDERER ---
for sp in db:
    # Basic Filter Logic
    if search.lower() in sp['scientific'].lower() or search.lower() in sp['local'].lower():
        with st.container():
            # Constructing the Card using Claude's visual hierarchy
            st.markdown(f"""
            <div class="species-card">
                <span class="sci-name">{sp['emoji']} {sp['scientific']}</span>
                <div class="local-name">"{sp['local']}" • {sp['mandarin']}</div>
                <hr style="border: 0.5px solid #2a3a28;">
                <div style="display: flex; justify-content: space-between;">
                    <span>🌍 {sp['habitat']}</span>
                    <span class="status-badge">{sp['status']}</span>
                </div>
                <p style="margin-top:10px; color: #8a9a7a;">{sp['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
			# Inside the expander, replace the old form
		# Inside the expander, replace the old form
with st.form(key=f"note_form_{sp['id']}"):
    new_note = st.text_area("Add Field Observation", placeholder="e.g. Observed flowering near riverbank...")
    submitted = st.form_submit_button("📤 Save to Google Sheet")
    if submitted and new_note:
        success, message = append_field_note(sp["scientific"], new_note, st.secrets["APPS_SCRIPT_URL"])
        if success:
            st.success(message)
            st.balloons()
        else:
            st.warning(message)
def append_field_note(scientific_name, note_text, webhook_url):
    """
    Sends a field note to the Google Apps Script web app.
    """
    # Sanitise
    safe_note = note_text.strip()
    safe_note = safe_note.replace("=", "﹦").replace("+", "＋").replace("@", "＠")
    safe_name = scientific_name.strip()
    
    payload = {
        "scientific": safe_name,
        "note": safe_note
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "Note saved successfully."
        else:
            return False, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        # Offline fallback – save to local queue
        queue_path = "data/offline_queue.json"
        queue_entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scientific": safe_name,
            "note": safe_note
        }
        queue = []
        if os.path.exists(queue_path):
            with open(queue_path, "r") as f:
                try:
                    queue = json.load(f)
                except:
                    pass
        queue.append(queue_entry)
        with open(queue_path, "w") as f:
            json.dump(queue, f, indent=2)
        return False, f"Offline – note saved locally. ({str(e)[:40]}...)"