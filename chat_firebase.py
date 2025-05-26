import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import streamlit as st

class ChatFirebase:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"],
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            })
            firebase_admin.initialize_app(cred, {
                'databaseURL': st.secrets["firebase"]["databaseURL"]
            })

    def send_message(self, room_id, sender_id, display_name, text):
        ref = db.reference(f"/rooms/{room_id}/messages")
        message = {
            "sender": sender_id,
            "display_name": display_name,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        ref.push(message)

    def get_messages(self, room_id):
        ref = db.reference(f"/rooms/{room_id}/messages")
        data = ref.get()
        if data:
            return sorted(data.values(), key=lambda m: m["timestamp"])
        return []

    def create_room(self, room_id, members, is_group=False):
        ref = db.reference(f"/rooms/{room_id}")
        ref.set({
            "members": members,
            "group": is_group,
            "messages": {}
        })

    def room_exists(self, room_id):
        return db.reference(f"/rooms/{room_id}").get() is not None
