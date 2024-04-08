import re
from typing import List

import instaloader
from instaloader import Profile
import instagrapi
from instagrapi.types import User


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
    if not profile.has_public_story:
        return (f'{start_text}'
                f'У <b>{profile.full_name}</b> в данный момент нет актуальных сторис.\n'
                f'Попробуй прошерстить этот аккаунт позже')
    else:
        if story.itemcount == 1:
            return (f'{start_text}'
                    f'У <b>{profile.full_name}</b> есть одна сторис - '
                    f'выложенная в {story.latest_media_local.strftime("%H:%M:%S")}.\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать эту сторис тебе.\n'
                    f'Прошерстить {profile.full_name}?')
        else:
            return (f'{start_text}'
                    f'У <b>{profile.full_name}</b> есть {str(story.itemcount)} сторис '
                    f'(последняя в {story.latest_media_local.strftime("%H:%M:%S")}).\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать все сторис тебе.\n'
                    f'Прошерстить {profile.full_name}?')

def create_user_text(user: User, stories: List[instagrapi.types.Story]) -> str:
    start_text = (f'{user.username}\n\n'
                  f'{user.full_name}\n'
                  f'{user.biography}\n\n\n'
                  f'<pre>Комментарий инсташершня:</pre>\n')
    if user.is_private:
        return (f'{start_text}'
                f'<b>{user.full_name}</b> - это закрытый профиль. Сторисы для просмотра недоступны')
    if len(stories) == 0:
        return (f'{start_text}'
                f'У <b>{user.full_name}</b> в данный момент нет актуальных сторис.\n'
                f'Попробуй прошерстить этот аккаунт позже')
    else:
        if len(stories) == 1:
            return (f'{start_text}'
                    f'У <b>{user.full_name}</b> есть одна сторис - '
                    f'выложенная в {stories[0].taken_at.strftime("%H:%M:%S")}.\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать эту сторис тебе.\n'
                    f'Прошерстить {user.full_name}?')
        else:
            return (f'{start_text}'
                    f'У <b>{user.full_name}</b> есть {str(len(stories))} сторис '
                    f'(последняя в {stories[-1].taken_at.strftime("%H:%M:%S")}).\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать все сторис тебе.\n'
                    f'Прошерстить {user.full_name}?')