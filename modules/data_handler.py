import pyrebase
import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

def get_firebase():
    # 1. Cloud Secrets
    if "firebase" in st.secrets:
        config = dict(st.secrets["firebase"])
    # 2. Local File
    else:
        config_path = Path("config/firebase_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            print("DEBUG: Config file missing!")
            return None
    return pyrebase.initialize_app(config)

def save_result_to_cloud(user_id, score, total, mood, token):
    """Saves data using the User's Auth Token."""
    print(f"DEBUG: Attempting to save for User {user_id}...")
    firebase = get_firebase()
    if not firebase: 
        print("DEBUG: Firebase init failed.")
        return False
    
    db = firebase.database()
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "mood": mood,
        "percentage": round((score/total)*100, 1)
    }
    
    try:
        # Pass the token to write to protected DB
        db.child("users").child(user_id).child("history").push(data, token=token)
        print("DEBUG: Save SUCCESS!")
        return True
    except Exception as e:
        print(f"DEBUG: Save FAILED. Error: {e}")
        return False

def load_history_from_cloud(user_id, token):
    """Loads data using the User's Auth Token."""
    print(f"DEBUG: Loading history for User {user_id}...")
    firebase = get_firebase()
    if not firebase: return []
    
    db = firebase.database()
    try:
        # Pass the token to read protected DB
        history = db.child("users").child(user_id).child("history").get(token=token).val()
        
        if not history: 
            print("DEBUG: No history found (Empty).")
            return []
            
        print(f"DEBUG: History loaded! Raw type: {type(history)}")
        
        if isinstance(history, dict):
            return list(history.values())
        if isinstance(history, list):
            return [x for x in history if x is not None]
            
        return []
    except Exception as e:
        print(f"DEBUG: Load FAILED. Error: {e}")
        return []