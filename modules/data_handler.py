# modules/data_handler.py
import json
import os
from datetime import datetime

DB_FILE = "user_progress.json"

def load_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_result(score, total, mood):
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "mood": mood,
        "percentage": round((score/total)*100, 1)
    }
    history.append(entry)
    with open(DB_FILE, "w") as f:
        json.dump(history, f, indent=4)
    return history