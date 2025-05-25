
class UserDatabase:
    def __init__(self):
        # Dữ liệu người dùng giả lập
        self.users = [
            {"id": "u1", "emotion": "happy", "name": "Alice"},
            {"id": "u2", "emotion": "sad", "name": "Bob"},
            {"id": "u3", "emotion": "angry", "name": "Charlie"},
            {"id": "u4", "emotion": "happy", "name": "Daisy"},
            {"id": "u5", "emotion": "neutral", "name": "Ethan"},
        ]

    def get_users_by_emotion(self, emotion):
        return [user for user in self.users if user["emotion"] == emotion]
