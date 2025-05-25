
import time
import firebase_admin
from firebase_admin import db

class MatchMaker:
    def __init__(self):
        self.waiting_list_ref = db.reference("/waiting_list")

    def find_match(self, emotion, user_id):
        candidates = self.waiting_list_ref.get()
        if not candidates:
            # Ghi mình vào danh sách chờ nếu chưa có ai
            self._add_to_waiting_list(emotion, user_id)
            return {"success": False}

        for uid, info in candidates.items():
            if uid != user_id and info.get("emotion") == emotion:
                # Tìm được người phù hợp → xóa cả 2 khỏi hàng đợi
                self.waiting_list_ref.child(uid).delete()
                return {
                    "success": True,
                    "partner_id": uid,
                    "partner_name": info.get("name", "Anonymous")
                }

        # Không tìm thấy → ghi mình vào hàng đợi
        self._add_to_waiting_list(emotion, user_id)
        return {"success": False}

    def _add_to_waiting_list(self, emotion, user_id):
        self.waiting_list_ref.child(user_id).set({
            "emotion": emotion,
            "timestamp": time.time()
        })
