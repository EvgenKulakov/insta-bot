from typing import List


class ProfileResponse:
    type: str
    text_message: str
    avatar_path: str

    def __init__(self, type: str, text_message: str, avatar_path: str | None = None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path


class StoryResponse:
    content: str
    path: str

    def __init__(self, content: str, path: str):
        self.content = content
        self.path = path