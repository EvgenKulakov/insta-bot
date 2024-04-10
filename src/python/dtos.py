from typing import List


class UserResponse:
    type: str
    text_message: str
    avatar_path: str
    username: str

    def __init__(self, type: str, text_message: str, avatar_path: str | None = None, username: str | None = None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path
        self.username = username


class ProfileResponse:
    type: str
    text_message: str
    avatar_path: str
    profile_id: int

    def __init__(self, type: str, text_message: str, avatar_path: str | None = None, profile_id: int | None = None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path
        self.profile_id = profile_id


class UserData:
    user_id: str
    username: str
    full_name: str

    def __init__(self, user_id: str, username: str, full_name: str):
        self.user_id = user_id
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


class StoryDataInstaloader:
    content: str
    path: str
    url: str

    def __init__(self, content: str, path: str, url: str):
        self.content = content
        self.path = path
        self.url = url


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


class StoryResponseInstaloader:
    full_name: str
    story_data_array: List[StoryDataInstaloader]
    count_stories: int
    count_viewed: int

    def __init__(self, full_name: str, story_data_array: List[StoryDataInstaloader] | None,
                 count_stories: int, count_viewed: int):
        self.full_name = full_name
        self.story_data_array = story_data_array
        self.count_stories = count_stories
        self.count_viewed = count_viewed