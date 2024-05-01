from typing import List
from instaloader import Profile


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
    username: str

    def __init__(self, type: str, text_message: str, avatar_path: str | None = None, username: str | None = None):
        self.type = type
        self.text_message = text_message
        self.avatar_path = avatar_path
        self.username = username


class ProfileDTO:
    username: str
    full_name: str
    userid: int
    is_private: bool
    followers: int
    followees: int
    biography: str
    profile_pic_url: str

    def __init__(self, profile: Profile):
        self.username = profile.username
        self.full_name = profile.full_name
        self.userid = profile.userid
        self.is_private = profile.is_private
        self.followers = profile.followers
        self.followees = profile.followees
        self.biography = profile.biography
        self.profile_pic_url = profile.profile_pic_url


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
    type: str
    callback_type: str
    username: str
    full_name: str | None
    story_data_array: List[StoryDataInstaloader] | None
    count_stories: int | None
    count_viewed: int | None
    folder_stories: str | None

    def __init__(self, type: str, callback_type: str, username: str, full_name: str | None = None,
                 story_data_array: List[StoryDataInstaloader] | None = None,count_stories: int | None = None,
                 count_viewed: int | None = None, folder_stories: str | None = None):
        self.type = type
        self.callback_type = callback_type
        self.username = username
        self.full_name = full_name
        self.story_data_array = story_data_array
        self.count_stories = count_stories
        self.count_viewed = count_viewed
        self.folder_stories = folder_stories