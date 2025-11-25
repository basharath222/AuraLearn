import pyrebase
import json
import os
from datetime import datetime
from pathlib import Path
import streamlit as st

def get_firebase():
    # 1. Try Environment Variables (Render / Universal Cloud)
    # This checks if the keys you added in Render Dashboard exist
    if os.getenv("FIREBASE_API_KEY"):
        config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        return pyrebase.initialize_app(config)

    # 2. Try Streamlit Secrets (Streamlit Cloud)
    # We wrap this in try/except so it doesn't crash if the secrets file is missing
    try:
        if "firebase" in st.secrets:
            config = dict(st.secrets["firebase"])
            return pyrebase.initialize_app(config)
    except:
        pass

    # 3. Try Local File (Localhost)
    config_path = Path("config/firebase_config.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        return pyrebase.initialize_app(config)
    
    return None

def save_result_to_cloud(user_id, score, total, mood, token=None):
    """Saves data using the User's Auth Token."""
    firebase = get_firebase()
    if not firebase: return False
    
    db = firebase.database()
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "mood": mood,
        "percentage": round((score/total)*100, 1)
    }
    
    try:
        if token:
            db.child("users").child(user_id).child("history").push(data, token=token)
        else:
            db.child("users").child(user_id).child("history").push(data)
        return True
    except Exception as e:
        print(f"Save Error: {e}")
        return False

def load_history_from_cloud(user_id, token=None):
    """Loads data using the User's Auth Token."""
    firebase = get_firebase()
    if not firebase: return []
    
    db = firebase.database()
    try:
        if token:
            history = db.child("users").child(user_id).child("history").get(token=token).val()
        else:
            history = db.child("users").child(user_id).child("history").get().val()
        
        if not history: return []
            
        if isinstance(history, dict):
            return list(history.values())
        if isinstance(history, list):
            return [x for x in history if x is not None]
            
        return []
    except Exception as e:
        print(f"Load Error: {e}")
        return []