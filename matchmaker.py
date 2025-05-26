import time
from firebase_admin import db

class MatchMaker:
    def __init__(self):
        self.waiting_list_ref = db.reference("/waiting_list")
        self.chat_rooms_ref = db.reference("/chat_rooms")

    def cleanup_stale_users(self):
        now = time.time()
        candidates = self.waiting_list_ref.get()
        if candidates:
            for uid, info in candidates.items():
                ts = info.get("timestamp", 0)
                if now - ts > 30:
                    print(f"[CLEANUP] Removing stale user {uid}")
                    self.waiting_list_ref.child(uid).delete()

    def find_match(self, emotion, user_id, name="Anonymous"):
        self.cleanup_stale_users()

        candidates = self.waiting_list_ref.get()
        print(f"[MatchMaker] Current waiting list: {candidates}")

        if not candidates:
            self._add_to_waiting_list(emotion, user_id, name)
            return {"success": False}

        for uid, info in candidates.items():
            if uid == user_id:
                continue  # ❌ Không tự match với chính mình

            partner_emotion = info.get("emotion")
            last_seen = info.get("timestamp", 0)
            is_recent = time.time() - last_seen <= 30

            if partner_emotion == emotion and is_recent:
                # ✅ Tạo phòng chat
                room_id = "_".join(sorted([user_id, uid]))
                self.chat_rooms_ref.child(room_id).set({
                    "members": [user_id, uid],
                    "timestamp": time.time()
                })

                # ✅ Xoá cả 2 người khỏi waiting_list
                self.waiting_list_ref.child(uid).delete()
                self.waiting_list_ref.child(user_id).delete()

                return {
                    "success": True,
                    "partner_id": uid,
                    "partner_name": info.get("name", "Anonymous")
                }

        # Nếu không tìm thấy ai phù hợp → thêm mình vào
        self._add_to_waiting_list(emotion, user_id, name)
        print(f"[MatchMaker] No match found. Added {user_id} to waitlist.")
        return {"success": False}

    def _add_to_waiting_list(self, emotion, user_id, name):
        self.waiting_list_ref.child(user_id).set({
            "emotion": emotion,
            "name": name,
            "timestamp": time.time()
        })
        print(f"[MatchMaker] Added {user_id} to waitlist with emotion {emotion}")
