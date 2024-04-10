from typing import List


class ProfileResponse:
    type: str
    text_message: str
    avatar_path: str
    user_id: str

    def __init__(self, type: str, text_message: str, avatar_path: str | None = None, user_id: str | None = None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path
        self.user_id = user_id


class UserData:
    username: str
    full_name: str

    def __init__(self, username: str, full_name: str):
        self.username = username
        self.full_name = full_name


class StoryData:
    content: str
    story_pk: str
    path: str
    filename: str

    def __init__(self, content: str, story_pk: str, path: str, filename: str):
        self.content = content
        self.story_pk = story_pk
        self.path = path
        self.filename = filename


class StoryResponse:
    full_name: str
    story_data_array: List[StoryData]
    count_stories: int
    count_viewed: int

    def __init__(self, full_name: str, story_data_array: List[StoryData] | None,
                 count_stories: int, count_viewed: int):
        self.full_name = full_name
        self.story_data_array = story_data_array
        self.count_stories = count_stories
        self.count_viewed = count_viewed