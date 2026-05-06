import requests
import json
import os

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