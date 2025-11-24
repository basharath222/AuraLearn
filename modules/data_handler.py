import pyrebase
import json
import os
import streamlit as st
from datetime import datetime

CONFIG_PATH = "config/firebase_config.json"

def get_firebase():
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH) as f:
        config = json.load(f)
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
    # Push to Firebase Realtime Database
    db.child("users").child(user_id).child("history").push(data)

def load_history_from_cloud(user_id):
    firebase = get_firebase()
    if not firebase: return []
    db = firebase.database()
    try:
        # Get data
        data = db.child("users").child(user_id).child("history").get().val()
        
        if not data:
            return []
            
        # Handle both Dictionary (Firebase default) and List formats
        if isinstance(data, dict):
            return list(data.values())
        elif isinstance(data, list):
            return [x for x in data if x is not None]
            
        return []
    except Exception as e:
        print(f"History Load Error: {e}")
        return []