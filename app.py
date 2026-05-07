import streamlit as st
import json
import os
import requests

# --- [NEW] SYNC LOGIC FOR OFFLINE QUEUE ---
def sync_offline_queue():
    queue_path = "data/offline_queue.json"
    if not os.path.exists(queue_path):
        st.info("No pending notes to sync.")
        return

    with open(queue_path, "r") as f:
        queue = json.load(f)

    if not queue:
        st.info("Queue is empty.")
        return

    success_count = 0
    url = st.secrets["APPS_SCRIPT_URL"]
    
    st.write(f"🔄 Syncing {len(queue)} notes...")
    
    remaining_queue = []
    for item in queue:
        try:
            resp = requests.post(url, json=item, timeout=10)
            if resp.status_code == 200:
                success_count += 1
            else:
                remaining_queue.append(item)
        except:
            remaining_queue.append(item)

    # Update the file with whatever failed to sync
    with open(queue_path, "w") as f:
        json.dump(remaining_queue, f)

    if success_count > 0:
        st.success(f"Successfully synced {success_count} notes to Google Sheets!")
        if not remaining_queue:
            os.remove(queue_path) # Clean up if all done
    else:
        st.error("Sync failed. Check connection.")

# --- DYNAMIC CSS (Claude's Enhanced Palette) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f1a0e; color: #d4c9a8; font-family: 'Georgia', serif; }
    
    /* Dynamic Card Border based on status classes we will inject */
    .species-card {
        background: #131d12;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-left: 5px solid #5a8a3c; /* Default Green */
    }
    .status-Endangered { border-left: 5px solid #ed8936 !important; }
    .status-Least_Concern { border-left: 5px solid #5a8a3c !important; }
    
    .sci-name { color: #c8d8a8; font-style: italic; font-size: 1.3rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: ADMIN CONTROLS ---
with st.sidebar:
    st.header("⚙️ Operator Tools")
    if st.button("🔄 Sync Offline Queue"):
        sync_offline_queue()
    
    st.markdown(f"""
        <div class="species-card {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="sci-name">{sp['emoji']} {sp['scientific']}</span>
                <img src="{sp.get('thumbnail_url', '')}" width="60" style="border-radius: 8px;">
            </div>
            <div style="color: #7a9a6a; font-size: 0.9rem;">"{sp['local']}" • {sp['mandarin']}</div>
            <hr style="border: 0.5px solid #2a3a28;">
            <p style="color: #8a9a7a;">{sp['description']}</p>
        </div>
    """, unsafe_allow_html=True)
    # ... (Rest of the expander logic) ...

# --- UTILITIES ---
def load_db():
    if os.path.exists("data/species_db.json"):
        with open("data/species_db.json", "r") as f:
            return json.load(f)
    return []

db = load_db()

# --- MAIN APP LOOP (Modified for Dynamic Status) ---
# ... (Assuming db is loaded) ...
for sp in db:
    status_class = "status-threatened" if sp.get("status_type") == "threatened" else "status-stable"

# --- HEADER ---
st.title("🌿 BIO-STACK")
st.caption("Wild West Sandbox · Taxonomy Engine v1.0")

# --- SECRETS CHECK ---
if "APPS_SCRIPT_URL" not in st.secrets:
    st.error("Missing `APPS_SCRIPT_URL` secret. Add it to your Streamlit Cloud secrets or `.streamlit/secrets.toml`.")
    st.stop()

search = st.text_input("🔍 Search specimen by name, habitat, or Mandarin...", "")

# --- CARD RENDERER ---
for sp in db:
    if search.lower() in sp['scientific'].lower() or search.lower() in sp['local'].lower():
        with st.container():
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
            
            with st.expander("📋 Full Taxonomy & Field Notes"):
                if "taxonomy" in sp:
                    st.table(sp["taxonomy"])
                else:
                    st.write("No taxonomy data available.")
                
                with st.form(key=f"note_form_{sp['id']}"):
                    new_note = st.text_area("Add Field Observation", placeholder="e.g. Observed flowering near riverbank...")
                    submitted = st.form_submit_button("📤 Save to Google Sheet")
                    if submitted and new_note:
                        success, message = append_field_note(
                            sp["scientific"],
                            new_note,
                            st.secrets["APPS_SCRIPT_URL"]
                        )
                        if success:
                            st.success(message)
                            st.balloons()
                        else:
                            st.warning(message)