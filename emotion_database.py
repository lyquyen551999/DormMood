import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import os
import streamlit as st

class EmotionDatabase:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                ...
            })
            firebase_admin.initialize_app(cred, {
                'databaseURL': st.secrets["firebase"]["databaseURL"]
            })
        self.db = firestore.client()

    def save_mood(self, user_id, mood, note):
        try:
            entry = {
                "mood": mood,
                "note": note,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.db.collection("moods").document(user_id).collection("entries").add(entry)
            return True
        except Exception as e:
            print("🔥 Error saving mood:", e)
            return False

    def load_moods(self, user_id):
        try:
            entries = self.db.collection("moods").document(user_id).collection("entries").stream()
            data = []
            for doc in entries:
                entry = doc.to_dict()
                data.append((doc.id, entry))
            data = sorted(data, key=lambda x: x[1]["timestamp"], reverse=True)
            return data
        except Exception as e:
            print("🔥 Error loading moods:", e)
            return []
