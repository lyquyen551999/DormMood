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
            if uid != user_id and info.get("emotion") == emotion:
                # Nếu đã offline quá 30 giây → loại bỏ
                if not info.get("is_online") or time.time() - info.get("timestamp", 0) > 30:
                    self.waiting_list_ref.child(uid).delete()
                    continue
                # ✅ Match hợp lệ
                self.waiting_list_ref.child(uid).delete()
                return {
                    "success": True,
                    "partner_id": uid,
                    "partner_name": info.get("name", "Anonymous")
                }

        # No match, add self to waiting list
        self._add_to_waiting_list(emotion, user_id, name)
        print(f"[MatchMaker] No match found. Added {user_id} to waitlist.")
        return {"success": False}

    def _add_to_waiting_list(self, emotion, user_id, name):
        self.waiting_list_ref.child(user_id).set({
            "emotion": emotion,
            "name": name,
            "timestamp": time.time(),
            "is_online": True
        })
        print(f"[MatchMaker] Added {user_id} to waitlist with emotion {emotion}")

    def cleanup_waitlist(self):
        now = time.time()
        candidates = self.waiting_list_ref.get()
        if not candidates:
            return

        for uid, info in candidates.items():
            ts = info.get("timestamp", 0)
            online = info.get("is_online", False)
            if not online or now - ts > 30:
                print(f"[CLEANUP] Removing {uid} from waitlist (offline/timeout)")
                self.waiting_list_ref.child(uid).delete()
