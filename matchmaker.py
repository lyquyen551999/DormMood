import time
from firebase_admin import db

class MatchMaker:
    def __init__(self):
        self.waiting_list_ref = db.reference("/waiting_list")

    def find_match(self, emotion, user_id, name="Anonymous"):
        candidates = self.waiting_list_ref.get()
        print(f"[MatchMaker] Current waiting list: {candidates}")

        if not candidates:
            self._add_to_waiting_list(emotion, user_id, name)
            return {"success": False}

        for uid, info in candidates.items():
            if uid == user_id:
                continue  # Không tự match với mình

            partner_emotion = info.get("emotion")
            last_seen = info.get("timestamp", 0)
            is_recent = time.time() - last_seen <= 30  # Chỉ giữ người vừa ping

            if partner_emotion == emotion and is_recent:
                # ✅ Tìm thấy người phù hợp và còn hoạt động
                self.waiting_list_ref.child(uid).delete()
                return {
                    "success": True,
                    "partner_id": uid,
                    "partner_name": info.get("name", "Anonymous")
                }
            else:
                # 🧹 Loại khỏi danh sách nếu quá 30s
                if not is_recent:
                    print(f"[CLEANUP] Removing {uid} from waitlist (stale)")
                    self.waiting_list_ref.child(uid).delete()

        # Không match được ai → thêm chính mình vào danh sách
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
