
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import uuid
import os

class ChatFirebase:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                ...
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
