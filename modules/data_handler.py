import pyrebase
import json
import os
import streamlit as st
from datetime import datetime
from pathlib import Path

# Cloud-Compatible Firebase Init
def get_db():
    try:
        # 1. Try Secrets (Cloud)
        if "firebase" in st.secrets:
            config = dict(st.secrets["firebase"])
        # 2. Try Local File
        else:
            config_path = Path("config/firebase_config.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                return None
        
        firebase = pyrebase.initialize_app(config)
        return firebase.database()
    except:
        return None

def save_result_to_cloud(user_id, score, total, mood):
    db = get_db()
    if not db: return False # Failed to connect

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "mood": mood,
        "percentage": round((score/total)*100, 1)
    }
    
    try:
        db.child("users").child(user_id).child("history").push(data)
        return True # Success
    except Exception as e:
        print(f"Save Error: {e}")
        return False

def load_history_from_cloud(user_id):
    db = get_db()
    if not db: return []

    try:
        data = db.child("users").child(user_id).child("history").get().val()
        if not data: return []
            
        if isinstance(data, dict):
            return list(data.values())
        elif isinstance(data, list):
            return [x for x in data if x is not None]
        return []
    except:
        return []