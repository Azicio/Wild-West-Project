import streamlit as st
import json
import os
import requests
import datetime

# --- CONFIG ---
st.set_page_config(page_title="Bio-Stack | Wild West", page_icon="🌿", layout="wide")

# --- DYNAMIC CSS (Claude's Enhanced Palette + IUCN status borders) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f1a0e;
        color: #d4c9a8;
        font-family: 'Georgia', serif;
    }

    .species-card {
        background: #131d12;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-left: 5px solid #5a8a3c;   /* default green */
    }

    /* IUCN-style border colours */
    .status-Least_Concern      { border-left: 5px solid #4caf50; }
    .status-Near_Threatened     { border-left: 5px solid #8bc34a; }
    .status-Vulnerable          { border-left: 5px solid #ffc107; }
    .status-Endangered          { border-left: 5px solid #ff9800; }
    .status-Critically_Endangered { border-left: 5px solid #f44336; }
    .status-Extinct_in_the_Wild  { border-left: 5px solid #9e9e9e; }
    .status-Extinct              { border-left: 5px solid #616161; }
    .status-Cultivated           { border-left: 5px solid #2196f3; }  /* for cultivated "stable" */

    .sci-name {
        color: #c8d8a8;
        font-style: italic;
        font-size: 1.3rem;
        font-weight: bold;
    }
    .local-name { color: #7a9a6a; font-size: 0.9rem; }
    .status-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        color: #fff;
        background: #5a8a3c;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GOOGLE SHEETS BRIDGE (unchanged) ---
def append_field_note(scientific_name, note_text, webhook_url):
    safe_note = note_text.strip()
    safe_note = safe_note.replace("=", "﹦").replace("+", "＋").replace("@", "＠")
    safe_name = scientific_name.strip()
    payload = {"scientific": safe_name, "note": safe_note}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "Note saved successfully."
        else:
            return False, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
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

# --- SYNC OFFLINE QUEUE (Gemini's addition) ---
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

    with open(queue_path, "w") as f:
        json.dump(remaining_queue, f)

    if success_count > 0:
        st.success(f"Successfully synced {success_count} notes to Google Sheets!")
        if not remaining_queue:
            os.remove(queue_path)
    else:
        st.error("Sync failed. Check connection.")

# --- UTILITIES ---
def load_db():
    if os.path.exists("data/species_db.json"):
        with open("data/species_db.json", "r") as f:
            return json.load(f)
    return []

def get_status_class(status_type):
    """Map an IUCN-style status to a CSS class (e.g. 'Least_Concern' → 'status-Least_Concern')"""
    if not status_type:
        return ""
    # Replace spaces/underscores to match our CSS class names
    return f"status-{status_type.replace(' ', '_')}"

db = load_db()

# --- HEADER ---
st.title("🌿 BIO-STACK")
st.caption("Wild West Sandbox · Taxonomy Engine v1.0")

# --- SIDEBAR: ADMIN CONTROLS ---
with st.sidebar:
    st.header("⚙️ Operator Tools")
    if st.button("🔄 Sync Offline Queue"):
        sync_offline_queue()

# --- SECRETS CHECK ---
if "APPS_SCRIPT_URL" not in st.secrets:
    st.error("Missing `APPS_SCRIPT_URL` secret. Add it to your Streamlit Cloud secrets or `.streamlit/secrets.toml`.")
    st.stop()

search = st.text_input("🔍 Search specimen by name, habitat, or Mandarin...", "")

# --- CARD RENDERER ---
for sp in db:
    if search.lower() in sp['scientific'].lower() or search.lower() in sp['local'].lower():
        # Determine the CSS class for the left border based on status_type
        status_class = get_status_class(sp.get('status_type', ''))

        with st.container():
            st.markdown(f"""
            <div class="species-card {status_class}">
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

            # Optional thumbnail – if your JSON has a 'thumbnail_url' key
            if sp.get("thumbnail_url"):
                st.image(sp["thumbnail_url"], width=120)

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