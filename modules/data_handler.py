import pyrebase
import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

def get_firebase():
    # Try Secrets (Cloud)
    if "firebase" in st.secrets:
        config = dict(st.secrets["firebase"])
    # Try Local File
    else:
        config_path = Path("config/firebase_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            return None
    
    return pyrebase.initialize_app(config)

def save_result_to_cloud(user_id, score, total, mood, token):
    """
    Saves data using the User's Auth Token.
    """
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
    
    # Pass the token to prove identity!
    db.child("users").child(user_id).child("history").push(data, token=token)

def load_history_from_cloud(user_id, token=None):
    """
    Loads data using the User's Auth Token to bypass security rules.
    """
    firebase = get_firebase()
    if not firebase: return []
    db = firebase.database()
    try:
        # FIX: Added token=token to prove identity
        data = db.child("users").child(user_id).child("history").get(token=token).val()
        
        if not data:
            return []
            
        if isinstance(data, dict):
            return list(data.values())
        elif isinstance(data, list):
            return [x for x in data if x is not None]
            
        return []
    except Exception as e:
        print(f"History Load Error: {e}")
        return []