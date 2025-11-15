import firebase_admin
from firebase_admin import credentials, auth, firestore
import json
import os

# Initialize Firebase
def init_firebase():
    config_path = os.path.join("config", "firebase_config.json")
    cred = credentials.Certificate(config_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()
