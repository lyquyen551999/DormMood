
from user_database import UserDatabase

class MatchMaker:
    def __init__(self):
        self.db = UserDatabase()

    def find_match(self, emotion, user_id):
        candidates = self.db.get_users_by_emotion(emotion)

        if not candidates:
            return {"success": False}

        # Tạm chọn người đầu tiên không phải chính mình
        match = next((u for u in candidates if u["id"] != user_id), None)

        if match:
            return {
                "success": True,
                "partner_id": match["id"],
                "partner_name": match.get("name", "Anonymous")
            }
        else:
            return {"success": False}
