

class ProfileResponse:
    type: str
    text_message: str
    avatar_path: str

    def __init__(self, type: str, text_message: str, avatar_path=None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path