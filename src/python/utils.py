import instaloader
from instaloader import Profile
from dtos import StoryDataInstaloader
import re
from typing import List
import os
from datetime import datetime, timedelta
from telebot.types import Message


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
    if not story:
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


def create_text_insta_error(message: Message, loader_username: str, exception: Exception):
    return (f'Пользователь {message.chat.first_name} пытался поискать сторисы, '
            f'но упал аккаунт {loader_username}\n'
            f'Лог ошипки:\n'
            f'{exception}')


def create_success_text(message: Message, loader_username: str):
    return (f'Успешная игра в инста-бота:\n'
            f'Жук: {message.chat.first_name}\n'
            f'Инста-акк: {loader_username}')


def create_text_menu(mode: str) -> str:
    text_mode: str = ''
    if mode == 'query':
        text_mode = (f'<b>● Новый запрос</b>'
                     f'\n○ Сразу прошерстить'
                     f'\n○ Удаление записей')
    if mode == 'analyzeNew':
        text_mode = (f'○ Новый запрос'
                     f'\n<b>● Сразу прошерстить</b>'
                     f'\n○ Удаление записей')
    if mode == 'remove':
        text_mode = (f'○ Новый запрос'
                     f'\n○ Сразу прошерстить'
                     f'\n<b>● Удаление записей</b>')

    return (f'🏃‍♀️ Ты в меню быстрых действий'
            f'\n\nРежимы:'
            f'\n{text_mode}')


def get_start_text():
    return (f'<b>Привет, я Инстаграмный шершень</b>'
            f'\n\n🔍 Введи username пользователя instagram, чтобы сделать запрос.'
            f'\n\n🔍 🐝 ❌ Нажми /menu, чтобы быстро делать запросы для тех пользователей, которые искались ранее.'
            f'\n\n🧐 Кнопка /start только для приветственного текста, чтобы сделать запрос её нажимать не нужно.')


def files_handler(story_data_array: List[StoryDataInstaloader], folder_stories: str):

    for story_data in story_data_array:
        os.truncate(story_data.path, 0)

    for file_name in os.listdir(folder_stories):
        date_story = datetime.strptime(file_name.split('_')[0], '%d-%m-%Y')
        if datetime.now() - date_story > timedelta(days=2):
            file_path = os.path.join(folder_stories, file_name)
            os.remove(file_path)