import instaloader
from instaloader import Profile
from dtos import StoryDataInstaloader
import re
from typing import List
import os
from datetime import datetime, timedelta


def valid_username(username: str) -> bool:
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    return re.match(pattern, username)

def create_profile_text(profile: Profile, story: instaloader.Story | None = None) -> str:
    start_text = (f'{profile.username}\n\n'
                  f'{profile.full_name}\n'
                  f'{profile.biography}\n\n\n'
                  f'<pre>Комментарий инсташершня:</pre>\n')
    if profile.is_private:
        return (f'{start_text}'
                f'<b>{profile.full_name}</b> - это закрытый профиль. Сторисы для просмотра недоступны')
    if story.itemcount == 0:
        return (f'{start_text}'
                f'У <b>{profile.full_name}</b> в данный момент нет актуальных сторис.\n'
                f'Попробуй прошерстить этот аккаунт позже')
    if story.itemcount == 1:
        return (f'{start_text}'
                f'У <b>{profile.full_name}</b> есть одна сторис - '
                f'выложенная в {story.latest_media_local.strftime("%H:%M:%S")}.\n'
                f'Я могу анонимно прошерстить этот аккаунт и переслать эту сторис тебе.\n'
                f'Прошерстить {profile.full_name}?')
    if story.itemcount > 1:
        return (f'{start_text}'
                f'У <b>{profile.full_name}</b> есть {str(story.itemcount)} сторис '
                f'(последняя в {story.latest_media_local.strftime("%H:%M:%S")}).\n'
                f'Я могу анонимно прошерстить этот аккаунт и переслать все сторис тебе.\n'
                f'Прошерстить {profile.full_name}?')


def files_handler(story_data_array: List[StoryDataInstaloader], folder_stories: str):

    for story_data in story_data_array:
        os.truncate(story_data.path, 0)

    for file_name in os.listdir(folder_stories):
        date_story = datetime.strptime(file_name.split('_')[0], '%d-%m-%Y')
        if datetime.now() - date_story > timedelta(days=2):
            file_path = os.path.join(folder_stories, file_name)
            os.remove(file_path)