import pyrebase
import json
import os
from datetime import datetime

CONFIG_PATH = "config/firebase_config.json"

def get_firebase():
    if not os.path.exists(CONFIG_PATH): return None
    with open(CONFIG_PATH) as f: config = json.load(f)
    return pyrebase.initialize_app(config)

def save_result_to_cloud(user_id, score, total, mood):
    firebase = get_firebase()
    if not firebase: return
    db = firebase.database()
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "mood": mood,
        "percentage": round((score/total)*100, 1)
    }
    try:
        db.child("users").child(user_id).child("history").push(data)
    except Exception as e:
        print(f"Save Error: {e}")

def load_history_from_cloud(user_id):
    firebase = get_firebase()
    if not firebase: return []
    db = firebase.database()
    try:
        # Get data (Returns a Dictionary or None)
        data = db.child("users").child(user_id).child("history").get().val()
        
        if not data: return []
            
        # Convert Firebase Dictionary to List
        if isinstance(data, dict):
            return list(data.values())
        elif isinstance(data, list):
            return [x for x in data if x is not None]
            
        return []
    except Exception as e:
        print(f"Load Error: {e}")
        return []