import itertools
import random
from telebot import TeleBot
from instaloader import Story
from lock_context_wrappers import InstaloaderWrapper
from telebot.types import Message
from configparser import ConfigParser
import os
from datetime import datetime
from dtos import ProfileResponse, StoryDataInstaloader, StoryResponseInstaloader, ProfileDTO
from profiles_cache import ProfilesCache
from utils import create_profile_text, create_text_insta_error, get_avatar_path
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from response_handler import ResponseHandler
from instaloader_iterator import InstaloaderIterator


class Loader:
    PROPERTIES: ConfigParser
    INSTALOADERS: InstaloaderIterator
    CURRENT_LOADER: InstaloaderWrapper | None
    CURRENT_PROFILE: ProfileDTO | None
    PROFILES_CACHE: ProfilesCache
    CURRENT_STORY: Story | None
    BOT: TeleBot
    EXECUTOR: ThreadPoolExecutor
    LOCK: Event
    ADMIN_ID: int
    RESPONSE_HANDLER: ResponseHandler

    def __init__(self, properties: ConfigParser, instaloaders: InstaloaderIterator,
                 bot: TeleBot, executor: ThreadPoolExecutor, profiles_cache: ProfilesCache):
        self.PROPERTIES = properties
        self.INSTALOADERS = instaloaders
        self.BOT = bot
        self.CURRENT_LOADER = None
        self.CURRENT_PROFILE = None
        self.PROFILES_CACHE = profiles_cache
        self.CURRENT_STORY = None
        self.EXECUTOR = executor
        self.LOCK = Event()
        self.ADMIN_ID = int(self.PROPERTIES['TELEGRAM']['ADMIN_ID'])
        self.RESPONSE_HANDLER = ResponseHandler(bot, self.LOCK, self.ADMIN_ID)

    def search_profile(self, username: str, message: Message, GLOBAL_LOCK: Event):
        status_bar = message.text

        if not self.PROFILES_CACHE.get_profile(username):
            event = Event()
            def search(event_stop: Event):
                self.download_status_bar(message, status_bar, 'Поиск аккаунта', event_stop)
                self.CURRENT_LOADER = self.INSTALOADERS.next()
                if self.CURRENT_LOADER:
                    def try_get_stores():
                        try:
                            profile = self.CURRENT_LOADER.profile_from_username(username, message.chat.id)
                            self.CURRENT_PROFILE = ProfileDTO(profile) if profile else None
                        except Exception as exception:
                            text = create_text_insta_error(message, self.CURRENT_LOADER.get_loader_username(), exception)
                            self.BOT.send_message(self.ADMIN_ID, text)

                            self.INSTALOADERS.remove(self.CURRENT_LOADER)
                            self.CURRENT_LOADER = self.INSTALOADERS.next()
                            if self.CURRENT_LOADER: try_get_stores()
                    try_get_stores()
            self.thread_handler(search, event)

            if not self.CURRENT_LOADER:
                GLOBAL_LOCK.clear()
                text_for_admin = f'Все инста-аккаунты обосрались во время запроса {message.chat.first_name}\nfunc: search_profile'
                self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
                status_bar += '\n❌ Поиск аккаунта'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                text_message = '❌ В данный момент нет ответа от Instagram, попробуй сделать запрос позже — через 15-20 минут.'
                self.RESPONSE_HANDLER.query_handler(ProfileResponse('error', text_message), message)
            elif self.CURRENT_PROFILE:
                status_bar += '\n✅ Аккаунт найден'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                self.profile_data(username, message, status_bar, GLOBAL_LOCK)
            else:
                GLOBAL_LOCK.clear()
                status_bar = message.text + '\n❌ Поиск аккаунта'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                text_message = f'Аккаунта "{username}" нет в инстаграм'
                self.RESPONSE_HANDLER.query_handler(ProfileResponse('error', text_message), message)
        else:
            status_bar += '\n✅ Аккаунт найден'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            self.profile_data(username, message, status_bar, GLOBAL_LOCK)

    def profile_data(self, username: str, message: Message, status_bar: str, GLOBAL_LOCK: Event):
        type_response: str
        text_message: str

        if self.CURRENT_PROFILE.is_private:
            type_response = 'private'
            text_message = create_profile_text(self.CURRENT_PROFILE)
        else:
            def search(event_stop: Event):
                self.download_status_bar(message, status_bar, 'Проверка сторис', event_stop)
                def try_get_stores():
                    try:
                        self.CURRENT_STORY = self.CURRENT_LOADER.loader_get_stories(self.CURRENT_PROFILE.userid)
                    except Exception as exception:
                        text = create_text_insta_error(message, self.CURRENT_LOADER.get_loader_username(), exception)
                        self.BOT.send_message(self.ADMIN_ID, text)

                        self.INSTALOADERS.remove(self.CURRENT_LOADER)
                        self.CURRENT_LOADER = self.INSTALOADERS.next()
                        if self.CURRENT_LOADER: try_get_stores()
                try_get_stores()
            self.thread_handler(search, Event())

            if not self.CURRENT_LOADER:
                GLOBAL_LOCK.clear()
                text_for_admin = f'Все инста-аккаунты обосрались во время запроса {message.chat.first_name}\nfunc: profile_data'
                self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
                status_bar += '\n❌ Информация о сторис'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                text_message = '❌ В данный момент нет ответа от Instagram, попробуй сделать запрос позже — через 15-20 минут.'
                self.RESPONSE_HANDLER.query_handler(ProfileResponse('error', text_message), message)
                return

            type_response = 'no_stories' if not self.CURRENT_STORY else 'has_stories'
            text_message = create_profile_text(self.CURRENT_PROFILE, self.CURRENT_STORY)

            status_bar += '\n✅ Информация о сторис'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        if not self.PROFILES_CACHE.get_profile(username):
            event = Event()
            self.download_status_bar(message, status_bar, 'Поиск фото', event)
            try:
                resp = self.CURRENT_LOADER.get_raw_dynamic_login(self.CURRENT_PROFILE.profile_pic_url, True)
                event.set()
                time.sleep(0.1)
                status_bar += '\n✅ Фото профиля'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

                folder_avatar = f"{self.PROPERTIES['PATHS']['PATH_OS']}cache/{self.CURRENT_PROFILE.username}/avatar"
                if not os.path.exists(folder_avatar):
                    os.makedirs(folder_avatar)
                date_avatar = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
                filename = date_avatar.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
                avatar_path = os.path.join(folder_avatar, filename)

                if not os.path.exists(avatar_path):
                    self.CURRENT_LOADER.write_raw_dynamic_login(resp, avatar_path, True)
                    print()

                self.PROFILES_CACHE.put_profile(self.CURRENT_PROFILE)
                GLOBAL_LOCK.clear()
                response = ProfileResponse(type_response, text_message, avatar_path, self.CURRENT_PROFILE.username)
                self.RESPONSE_HANDLER.query_handler(response, message, self.CURRENT_LOADER.get_loader_username())
            except Exception as exception:
                GLOBAL_LOCK.clear()
                event.set()
                time.sleep(0.1)
                status_bar += '\n❌ Фото профиля'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                text_for_admin = (f'НЕОБРАБОТАНЫЙ обсёр во время запроса фото: login_context '
                                  f'{message.chat.first_name}\nлог: {exception}')
                self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
                text_message = '❌ В данный момент нет ответа от Instagram, попробуй сделать запрос позже — через 15-20 минут.'
                self.RESPONSE_HANDLER.query_handler(ProfileResponse('error', text_message), message)
        else:
            GLOBAL_LOCK.clear()
            status_bar += '\n✅ Фото профиля'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            folder_avatar = f"{self.PROPERTIES['PATHS']['PATH_OS']}cache/{self.CURRENT_PROFILE.username}/avatar"
            avatar_path = get_avatar_path(folder_avatar)
            response = ProfileResponse(type_response, text_message, avatar_path, self.CURRENT_PROFILE.username)
            self.RESPONSE_HANDLER.query_handler(response, message, self.CURRENT_LOADER.get_loader_username())


    def download_stories(self, callback_type: str, username: str, status_message: Message,
                         src_message: Message, time_created: str, GLOBAL_LOCK: Event):

        status_bar = status_message.text
        self.CURRENT_LOADER = self.INSTALOADERS.get_without_iteration()

        if not self.CURRENT_LOADER:
            GLOBAL_LOCK.clear()
            text_for_admin = (f'Все инста-аккаунты обосрались во время запроса {status_message.chat.first_name}'
                              f'\nfunc: download_stories (begin)')
            self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
            response = StoryResponseInstaloader('error_loader', callback_type, username)
            self.RESPONSE_HANDLER.hornet_handler(response, src_message)
            return

        if (not self.CURRENT_PROFILE or self.CURRENT_PROFILE.username != username
                or not self.CURRENT_STORY or int(time.time()) - int(time_created) > 600):

            self.CURRENT_LOADER = self.INSTALOADERS.next()

            if not self.CURRENT_PROFILE or self.CURRENT_PROFILE.username != username:
                self.CURRENT_PROFILE = self.PROFILES_CACHE.get_profile(username)

                if not self.CURRENT_PROFILE:
                    event = Event()
                    def search(event_stop: Event):
                        self.download_status_bar(status_message, status_bar, 'Поиск аккаунта', event_stop, 2)
                        if self.CURRENT_LOADER:
                            def try_get_stores():
                                try:
                                    profile = self.CURRENT_LOADER.profile_from_username(username, src_message.chat.id)
                                    self.CURRENT_PROFILE = ProfileDTO(profile) if profile else None
                                    self.PROFILES_CACHE.put_profile(self.CURRENT_PROFILE)
                                except Exception as exception:
                                    text = create_text_insta_error(status_message,
                                                                   self.CURRENT_LOADER.get_loader_username(), exception)
                                    self.BOT.send_message(self.ADMIN_ID, text)
                                    self.INSTALOADERS.remove(self.CURRENT_LOADER)
                                    self.CURRENT_LOADER = self.INSTALOADERS.next()
                                    if self.CURRENT_LOADER: try_get_stores()
                            try_get_stores()
                    self.thread_handler(search, event)

                    if not self.CURRENT_LOADER:
                        GLOBAL_LOCK.clear()
                        status_bar += '\n\n❌ Поиск аккаунта'
                        self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)
                        text_for_admin = (f'Все инста-аккаунты обосрались во время запроса {status_message.chat.first_name}'
                                          f'\nfunc: download_stories (search profile)')
                        self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
                        response = StoryResponseInstaloader('error_loader', callback_type, username)
                        self.RESPONSE_HANDLER.hornet_handler(response, src_message)
                        return

                    status_bar += '\n\n✅ Аккаунт найден'
                    self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)

            count_idents = 1 if 'Аккаунт найден' in status_bar else 2
            def search(event_stop: Event):
                self.download_status_bar(status_message, status_bar, 'Поиск сторис', event_stop, count_idents=count_idents)
                if self.CURRENT_LOADER:
                    def try_get_stores():
                        try:
                            self.CURRENT_STORY = self.CURRENT_LOADER.loader_get_stories(self.CURRENT_PROFILE.userid)
                        except Exception as ex:
                            text = create_text_insta_error(status_message, self.CURRENT_LOADER.get_loader_username(), ex)
                            self.BOT.send_message(self.ADMIN_ID, text)

                            self.INSTALOADERS.remove(self.CURRENT_LOADER)
                            self.CURRENT_LOADER = self.INSTALOADERS.next()
                            if self.CURRENT_LOADER: try_get_stores()
                    try_get_stores()
            self.thread_handler(search, Event())

            idents = '\n' * count_idents
            if self.CURRENT_LOADER and self.CURRENT_STORY:
                status_bar += f'{idents}✅ Сторис найдены'
                self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)
            else:
                GLOBAL_LOCK.clear()
                status_bar += f'{idents}❌ Сторис не найдены'
                self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)
                if not self.CURRENT_LOADER:
                    text_for_admin = (f'Все инста-аккаунты обосрались во время запроса {status_message.chat.first_name}'
                                      f'\nfunc: download_stories (search stories)')
                    self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
                    response = StoryResponseInstaloader('error_loader', callback_type, username)
                    self.RESPONSE_HANDLER.hornet_handler(response, src_message)
                    return
                if not self.CURRENT_STORY:
                    response = StoryResponseInstaloader('no_stories', callback_type, username, self.CURRENT_PROFILE.full_name)
                    self.RESPONSE_HANDLER.hornet_handler(response, src_message, self.CURRENT_LOADER.get_loader_username())
                    return

        folder_stories = f"{self.PROPERTIES['PATHS']['PATH_OS']}cache/{self.CURRENT_PROFILE.username}/stories"
        if not os.path.exists(folder_stories):
            os.makedirs(folder_stories)

        story_data_array = []
        count_viewed = 0

        for item in self.CURRENT_STORY._node['items']:
            date_local = datetime.fromtimestamp(item['taken_at_timestamp']).astimezone()
            filename = date_local.strftime('%d-%m-%Y_%H-%M-%S') + f'_{str(status_message.chat.id)}'
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

        count_downloads = 0

        if count_viewed > 0:
            status_bar += (f'\n\nАктуальных сторис: {self.CURRENT_STORY.itemcount}'
                           f'\nСкачано ранее: {count_viewed}')
        if story_data_array:
            status_bar += f'\n\nЗагружено: [{count_downloads}/{len(story_data_array)}]'
        self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)

        login_bool = random.choice([True, False])
        try:
            for story_data in story_data_array:
                resp = self.CURRENT_LOADER.get_raw_dynamic_login(story_data.url, login_bool)
                self.CURRENT_LOADER.write_raw_dynamic_login(resp, story_data.path, login_bool)
                print()
                status_bar = status_bar.replace(f'[{count_downloads}/{len(story_data_array)}]',
                                                f'[{count_downloads + 1}/{len(story_data_array)}]')
                self.BOT.edit_message_text(status_bar, status_message.chat.id, status_message.message_id)
                count_downloads += 1
        except Exception as exception:
            GLOBAL_LOCK.clear()
            text_for_admin = (f'НЕОБРАБОТАНЫЙ обсёр во время загрузки сториз: dynamic_context(login_bool:{login_bool}) '
                              f'{src_message.chat.first_name}\nлог: {exception}')
            self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)
            text_message = '❌ В данный момент нет ответа от Instagram, попробуй сделать запрос позже — через 15-20 минут.'
            self.RESPONSE_HANDLER.query_handler(ProfileResponse('error', text_message), src_message)
            return

        GLOBAL_LOCK.clear()
        response = StoryResponseInstaloader('has_stories', callback_type, username, self.CURRENT_PROFILE.full_name,
                                            story_data_array, self.CURRENT_STORY.itemcount, count_viewed, folder_stories)
        self.CURRENT_STORY = None
        self.RESPONSE_HANDLER.hornet_handler(response, src_message, self.CURRENT_LOADER.get_loader_username(), login_bool)


    def download_status_bar(self, message: Message, status_bar: str, text_search: str,
                            event_stop: Event, count_idents: int = 1):
        smiles = ['◽', '◾']
        idents = '\n' * count_idents

        smile_cycle = itertools.cycle(smiles)

        def await_load(event: Event):
            while not event.is_set():
                text = f'{status_bar}{idents}{next(smile_cycle)} {text_search}'
                self.BOT.edit_message_text(text, message.chat.id, message.message_id)
                time.sleep(0.4)

        self.EXECUTOR.submit(lambda: await_load(event_stop))

    def thread_handler(self, func, event_stop: Event):
        func(event_stop)
        event_stop.set()
        time.sleep(0.1)