from instagrapi import Client
from instagrapi.exceptions import LoginRequired, UserNotFound
from instagrapi.types import Story, User
from telebot import TeleBot
from telebot.types import Message
import os
import time
from typing import List
from configparser import ConfigParser
from dtos import ProfileResponse
from utils import create_user_text


class Loader:
    CLIENT: Client
    STORIES: List[Story]
    BOT: TeleBot
    PROPERTIES: ConfigParser
    def __init__(self, properties: ConfigParser, BOT: TeleBot):
        self.CLIENT = Client()
        self.BOT = BOT
        self.PROPERTIES = properties

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
                except LoginRequired:
                    self.BOT.send_message(admin_id, 'Сессия instagrapi не валидна, будет попытка с uuids')
                    print("Session is invalid, need to login via username and password")
                    old_session = self.CLIENT.get_settings()
                    self.CLIENT.set_settings({})
                    self.CLIENT.set_uuids(old_session["uuids"])
                    self.CLIENT.login(username, password)
            except Exception as e:
                text = (f'Ошибка:\n'
                        f'Couldn\'t login user using session information: {e}\n'
                        f'Будет попытка войти через instaloader')
                self.BOT.send_message(admin_id, text)
                print("Couldn't login user using session information: %s" % e)

        sign_in_session()

    def user_info(self, message: Message, username: str | None = None,
                  user_id: str | None = None) -> ProfileResponse:
        user: User
        status_bar: str

        # account search
        if username:
            try:
                user = self.CLIENT.user_info_by_username_v1(username)
            except UserNotFound:
                text_message = f'❌ Аккаунта "{username}" нет в инстаграм'
                return ProfileResponse('error', text_message)
        else:
            user = self.CLIENT.user_info_v1(user_id)
        status_bar = message.text + '\n✅ Аккаунт найден'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        # stories search
        self.STORIES = self.CLIENT.user_stories(user.pk)
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
            self.CLIENT.photo_download_by_url(str(user.profile_pic_url), filename, folder_avatar)
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

        return ProfileResponse(type_response, text_message, avatar_path, user.pk)


# def download():
#     time_start = time.time()
#
#     username_for_load = 'anichkina_a'
#
#     user = cl.user_info_by_username_v1(username_for_load)
#
#     print('user найден')
#     print(time.time() - time_start)
#
#     user_stories = cl.user_stories(user.pk)
#     print('cl.user_stories')
#     print(time.time() - time_start)
#
#     folder = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{username_for_load + "v2"}/stories'
#     if not os.path.exists(folder):
#         os.makedirs(folder)
#
#
#     for story in user_stories:
#         filename = story.taken_at.strftime('%d-%m-%Y_%H-%M-%S') + f'_{str(123123)}'
#         cl.story_download(story.pk, filename, folder)
#         print(cl.story_info(story.pk))
#         for k, v in vars(story).items():
#             print(f'key: {k} val: {v}')
#
#     print(user_stories)
#
#     time_end = time.time()
#     print(time_end - time_start)
#
#
# download()