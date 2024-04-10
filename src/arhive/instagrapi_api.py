from instagrapi import Client
from instagrapi.exceptions import LoginRequired, UserNotFound
from instagrapi.types import Story, User
from telebot import TeleBot
from telebot.types import Message
import os
import time
from typing import List, Dict
from configparser import ConfigParser
from dtos import UserResponse, StoryResponse, StoryData, UserData
from utils import create_user_text


class Loader:
    CLIENT: Client
    BOT: TeleBot
    PROPERTIES: ConfigParser
    USERS_CACHE: Dict[str, UserData]
    STORIES: List[Story]
    def __init__(self, properties: ConfigParser, BOT: TeleBot):
        self.CLIENT = Client()
        self.BOT = BOT
        self.PROPERTIES = properties
        self.USERS_CACHE = {}
        self.STORIES = None

        def sign_in_session():
            username = self.PROPERTIES['INSTAGRAM']['USER']
            password = self.PROPERTIES['INSTAGRAM']['PASSWORD']
            session = self.CLIENT.load_settings(self.PROPERTIES['INSTAGRAM']['DUMP'])
            admin_id = int(self.PROPERTIES['TELEGRAM']['ADMIN_ID'])

            try:
                self.CLIENT.set_settings(session)
                self.CLIENT.login(username, password)
                try:
                    self.CLIENT.get_timeline_feed()
                    self.BOT.send_message(admin_id, '✅ instagrapi login')
                except LoginRequired:
                    self.BOT.send_message(admin_id, 'Сессия instagrapi не валидна, будет попытка с uuids')
                    print("Session is invalid, need to login via username and password")
                    old_session = self.CLIENT.get_settings()
                    self.CLIENT.set_settings({})
                    self.CLIENT.set_uuids(old_session["uuids"])
                    self.CLIENT.login(username, password)
                    self.CLIENT.dump_settings(properties['INSTAGRAM']['DUMP_NEW'])
            except Exception as e:
                text = (f'Ошибка:\n'
                        f'Couldn\'t login user using session information: {e}\n'
                        f'Будет попытка войти через instaloader')
                self.BOT.send_message(admin_id, text)
                print("Couldn't login user using session information: %s" % e)

        sign_in_session()

    def user_info(self, message: Message, username: str) -> UserResponse:
        user: User
        status_bar: str

        # account search
        try:
            user = self.CLIENT.user_info_by_username_v1(username)
        except UserNotFound:
            text_message = f'❌ Аккаунта "{username}" нет в инстаграм'
            return UserResponse('error', text_message)
        status_bar = message.text + '\n✅ Аккаунт найден'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        self.USERS_CACHE[username] = UserData(user.pk, user.username, user.full_name)

        # stories search
        self.STORIES = self.CLIENT.user_stories_v1(user.pk)
        status_bar += '\n✅ Информация о сторис'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        # avatar download
        folder_avatar = f"{self.PROPERTIES['INSTAGRAM']['CACHE_PATH']}/{user.username}/avatar"
        if not os.path.exists(folder_avatar):
            os.makedirs(folder_avatar)
        filename = 'avatar-default' # Сделать уникальный filename
        avatar_path = os.path.join(folder_avatar, filename + '.jpg')
        if not os.path.isfile(avatar_path):
            os.mknod(avatar_path)
            self.CLIENT.photo_download_by_url(str(user.profile_pic_url_hd), filename, folder_avatar)
        status_bar += '\n✅ Фото профиля'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        # type response and text message
        if user.is_private:
            type_response = 'private'
        elif len(self.STORIES) == 0:
            type_response = 'no_stories'
        else:
            type_response = 'has_stories'
        text_message = create_user_text(user, self.STORIES)

        return UserResponse(type_response, text_message, avatar_path, username)

    def download_stories(self, username: str, message: Message, time_create: str) -> StoryResponse | None:
        status_bar = message.text
        user_data = self.USERS_CACHE.get(username)

        if not user_data:
            status_bar += '\n\nПоиск аккаунта'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            user = self.CLIENT.user_info_by_username_v1(username)
            user_data = UserData(user.pk, user.username, user.full_name)
            self.USERS_CACHE[username] = user_data
            status_bar = status_bar.replace('Поиск аккаунта', '✅ Аккаунт найден')
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        if (not self.STORIES or len(self.STORIES) == 0 or self.STORIES[0].user.pk != user_data.user_id
                or int(time.time()) - int(time_create) > 600):

            if 'Аккаунт найден' in status_bar:
                status_bar += '\nПоиск сторис'
            else:
                status_bar += '\n\nПоиск сторис'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            self.STORIES = self.CLIENT.user_stories_v1(user_data.user_id)

            if len(self.STORIES) > 0:
                status_bar = status_bar.replace('Поиск сторис', '✅ Сторис найдены')
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            else:
                status_bar = status_bar.replace('Поиск сторис', '❌ Сторис не найдены')
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                return None

        folder_stories = f"{self.PROPERTIES['INSTAGRAM']['CACHE_PATH']}/{user_data.username}/stories"
        if not os.path.exists(folder_stories):
            os.makedirs(folder_stories)

        story_data_array = []
        count_viewed = 0

        for story in self.STORIES:
            filename = story.taken_at.strftime('%d-%m-%Y_%H-%M-%S') + f'_{str(message.chat.id)}'
            path = os.path.join(folder_stories, filename)

            if story.media_type == 2:
                if not os.path.isfile(path + '.mp4'):
                    story_data_array.append(StoryData('video', story.pk, path + '.mp4', filename))
                else:
                    count_viewed += 1
            else:
                if not os.path.isfile(path + ".jpg"):
                    story_data_array.append(StoryData('photo', story.pk, path + '.jpg', filename))
                else:
                    count_viewed += 1

        count_downloads = 0

        if count_viewed > 0:
            status_bar += (f'\n\nАктуальных сторис: {len(self.STORIES)}'
                           f'\nСкачано ранее: {count_viewed}')
            if story_data_array:
                status_bar += f'\n\nЗагружено: [{count_downloads}/{len(story_data_array)}]'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
        else:
            status_bar += f'\n\nЗагружено: [{count_downloads}/{len(self.STORIES)}]'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        for story_data in story_data_array:
            self.CLIENT.story_download(story_data.story_pk, story_data.filename, folder_stories)
            status_bar = status_bar.replace(f'[{count_downloads}/{len(story_data_array)}]',
                                            f'[{count_downloads + 1}/{len(story_data_array)}]')
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            count_downloads += 1

        response = StoryResponse(user_data.full_name, story_data_array, len(self.STORIES), count_viewed)
        self.STORIES = None
        return response