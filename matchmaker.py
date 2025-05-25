
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
                # Match found, remove both users
                self.waiting_list_ref.child(uid).delete()
                print(f"[MatchMaker] Match found with {uid}")
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
            "timestamp": time.time()
        })
        print(f"[MatchMaker] Added {user_id} to waitlist with emotion {emotion}")
