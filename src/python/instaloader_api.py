import itertools
import telebot
from instaloader import Instaloader, Profile, ProfileNotExistsException, Story, StoryItem
from telebot import TeleBot
from telebot.types import Message
from configparser import ConfigParser
import os
from datetime import datetime
from dtos import ProfileResponse, StoryDataInstaloader, StoryResponseInstaloader
from utils import create_profile_text
from typing import Dict
import configparser
import time
from concurrent.futures import ThreadPoolExecutor


class Loader:
    PROPERTIES: ConfigParser
    INSTALOADER: Instaloader
    LOADER_WITHOUT_LOGIN: Instaloader
    CURRENT_PROFILE: Profile | None
    PROFILES_CACHE: Dict[str, Profile]
    CURRENT_STORY: Story | None
    BOT: TeleBot
    STOP_SEARCH: bool
    EXECUTOR: ThreadPoolExecutor
    def __init__(self, properties: ConfigParser, BOT: TeleBot):
        self.PROPERTIES = properties
        user = self.PROPERTIES['INSTAGRAM']['USER']
        session_token = self.PROPERTIES['INSTAGRAM']['TOKEN']

        self.INSTALOADER = Instaloader()
        self.INSTALOADER.load_session_from_file(user, session_token)
        self.LOADER_WITHOUT_LOGIN = Instaloader()
        self.CURRENT_PROFILE = None
        self.PROFILES_CACHE = {}
        self.CURRENT_STORY = None
        self.BOT = BOT
        self.STOP_SEARCH = False
        self.EXECUTOR = ThreadPoolExecutor(max_workers=1)
        self.BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='✅ INSTALOADER start')

    def search_profile(self, username: str, message: Message) -> ProfileResponse:
        try:
            status_bar = message.text

            def search():
                self.download_status_bar(message, status_bar, 'Поиск аккаунта')
                self.CURRENT_PROFILE = Profile.from_username(self.LOADER_WITHOUT_LOGIN.context, username)
                self.PROFILES_CACHE[self.CURRENT_PROFILE.username] = self.CURRENT_PROFILE
            self.thread_handler(search)

            status_bar += '\n✅ Аккаунт найден'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            return self.profile_data(message, status_bar)
        except ProfileNotExistsException:
            self.STOP_SEARCH = True
            time.sleep(0.1)
            status_bar = message.text + '\n❌ Поиск аккаунта'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            text_message = f'Аккаунта "{username}" нет в инстаграм'
            return ProfileResponse('error', text_message)

    def profile_data(self, message: Message, status_bar: str) -> ProfileResponse:
        type_response: str
        text_message: str

        if self.CURRENT_PROFILE.is_private:
            type_response = 'private'
            text_message = create_profile_text(self.CURRENT_PROFILE)
        else:
            def search():
                self.download_status_bar(message, status_bar, 'Проверка сторис')
                self.CURRENT_STORY = next(self.INSTALOADER.get_stories([self.CURRENT_PROFILE.userid]))
            self.thread_handler(search)

            type_response = 'no_stories' if self.CURRENT_STORY.itemcount == 0 else 'has_stories'
            text_message = create_profile_text(self.CURRENT_PROFILE, self.CURRENT_STORY)

            status_bar += '\n✅ Информация о сторис'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        self.STOP_SEARCH = False
        self.download_status_bar(message, status_bar, 'Поиск фото')
        resp = self.LOADER_WITHOUT_LOGIN.context.get_raw(str(self.CURRENT_PROFILE.profile_pic_url))
        self.STOP_SEARCH = True
        time.sleep(0.1)
        status_bar += '\n✅ Фото профиля'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        folder_avatar = f"{self.PROPERTIES['INSTAGRAM']['CACHE_PATH']}/{self.CURRENT_PROFILE.username}/avatar"
        if not os.path.exists(folder_avatar):
            os.makedirs(folder_avatar)
        date_avatar = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
        filename = date_avatar.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
        avatar_path = os.path.join(folder_avatar, filename)

        if not os.path.exists(avatar_path):
            self.LOADER_WITHOUT_LOGIN.context.write_raw(resp, avatar_path)
            print()

        return ProfileResponse(type_response, text_message, avatar_path, self.CURRENT_PROFILE.username)

    def download_stories(self, username: str, message: Message, time_created: str) -> StoryResponseInstaloader | None:
        self.CURRENT_PROFILE = self.PROFILES_CACHE.get(username)
        status_bar = message.text
        if not self.CURRENT_PROFILE or not self.CURRENT_STORY or int(time.time()) - int(time_created) > 600:
            if not self.CURRENT_PROFILE:
                def search():
                    self.download_status_bar(message, status_bar, 'Поиск аккаунта', count_idents=2)
                    self.CURRENT_PROFILE = Profile.from_username(self.LOADER_WITHOUT_LOGIN.context, username)
                    self.PROFILES_CACHE[self.CURRENT_PROFILE.username] = self.CURRENT_PROFILE
                self.thread_handler(search)

                status_bar += '\n\n✅ Аккаунт найден'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

            count_idents = 1 if 'Аккаунт найден' in status_bar else 2
            def search():
                self.download_status_bar(message, status_bar, 'Поиск сторис', count_idents=count_idents)
                self.CURRENT_STORY = next(self.INSTALOADER.get_stories([self.CURRENT_PROFILE.userid]))
            self.thread_handler(search)

            idents = '\n' * count_idents
            if self.CURRENT_STORY and self.CURRENT_STORY.itemcount > 0:
                status_bar += f'{idents}✅ Сторис найдены'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            else:
                status_bar += f'{idents}❌ Сторис не найдены'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                return None

        # self.STOP_SEARCH = False
        # self.download_status_bar(message, status_bar, 'Подготовка загрузки', count_idents=2)

        folder_stories = f"{self.PROPERTIES['INSTAGRAM']['CACHE_PATH']}/{self.CURRENT_PROFILE.username}/stories"
        if not os.path.exists(folder_stories):
            os.makedirs(folder_stories)

        story_data_array = []
        count_viewed = 0

        for item in self.CURRENT_STORY._node['items']:
            date_local = datetime.fromtimestamp(item['taken_at_timestamp']).astimezone()
            filename = date_local.strftime('%d-%m-%Y_%H-%M-%S') + f'_{str(message.chat.id)}'
            path = os.path.join(folder_stories, filename)

            if item['is_video']:
                if not os.path.exists(path + '.mp4'):
                    video_url = item['video_resources'][-1]['src']
                    story_data_array.append(StoryDataInstaloader('video', path + '.mp4', video_url))
                else: count_viewed += 1
            else:
                if not os.path.exists(path + ".jpg"):
                    photo_url = item['display_resources'][-1]['src']
                    story_data_array.append(StoryDataInstaloader('photo', path + '.jpg', photo_url))
                else: count_viewed += 1

        # self.STOP_SEARCH = True
        # time.sleep(0.1)

        count_downloads = 0

        if count_viewed > 0:
            status_bar += (f'\n\nАктуальных сторис: {self.CURRENT_STORY.itemcount}'
                           f'\nСкачано ранее: {count_viewed}')
        if story_data_array:
            status_bar += f'\n\nЗагружено: [{count_downloads}/{len(story_data_array)}]'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        for story_data in story_data_array:
            resp = self.LOADER_WITHOUT_LOGIN.context.get_raw(story_data.url)
            self.LOADER_WITHOUT_LOGIN.context.write_raw(resp, story_data.path)
            print()
            status_bar = status_bar.replace(f'[{count_downloads}/{len(story_data_array)}]',
                                            f'[{count_downloads + 1}/{len(story_data_array)}]')
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            count_downloads += 1

        response = StoryResponseInstaloader(self.CURRENT_PROFILE.full_name, story_data_array,
                                            self.CURRENT_STORY.itemcount, count_viewed, folder_stories)
        self.CURRENT_STORY = None
        return response


    def download_status_bar(self, message: Message, status_bar: str, text_search: str, count_idents: int = 1):
        smiles = ['◽', '◾']
        idents = '\n' * count_idents

        smile_cycle = itertools.cycle(smiles)

        def await_load():
            while not self.STOP_SEARCH:
                text = f'{status_bar}{idents}{next(smile_cycle)} {text_search}'
                self.BOT.edit_message_text(text, message.chat.id, message.message_id)
                time.sleep(0.4)

        self.EXECUTOR.submit(await_load)

    def thread_handler(self, func):
        self.STOP_SEARCH = False
        func()
        self.STOP_SEARCH = True
        time.sleep(0.1)


# def all_load():
#     properties = configparser.ConfigParser()
#     properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')
#     loader = Loader(properties, telebot.TeleBot(properties['TELEGRAM']['BOT']))
#     loader.LOADER_WITHOUT_LOGIN.download_profile('username')