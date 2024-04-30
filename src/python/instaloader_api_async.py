import itertools
from telebot.async_telebot import AsyncTeleBot
from instaloader import Instaloader, Profile, ProfileNotExistsException, Story, StoryItem
from telebot.types import Message
from configparser import ConfigParser
import os
from datetime import datetime
from dtos import ProfileResponse, StoryDataInstaloader, StoryResponseInstaloader
from utils import create_profile_text, create_text_insta_error
from typing import Dict, Iterator
import time
from threading import Event
from database_service import Service
import asyncio
from concurrent.futures import ThreadPoolExecutor
from async_executor import AsyncExecutor

# EXECUTOR = AsyncExecutor()


class Loader:
    PROPERTIES: ConfigParser
    INSTALOADERS: Iterator[Instaloader]
    CURRENT_LOADER: Instaloader | None
    LOADER_WITHOUT_LOGIN: Instaloader
    CURRENT_PROFILE: Profile | None
    PROFILES_CACHE: Dict[str, Profile]
    CURRENT_STORY: Story | None
    ASYNC_BOT: AsyncTeleBot
    SERVICE: Service
    LOCK: Event

    def __init__(self, properties: ConfigParser, ASYNC_BOT: AsyncTeleBot, SERVICE: Service):
        self.PROPERTIES = properties
        self.ASYNC_BOT = ASYNC_BOT
        def loaders_init() -> Iterator[Instaloader]:
            user_1 = self.PROPERTIES['INSTAGRAM']['USER_1']
            # user_2 = self.PROPERTIES['INSTAGRAM']['USER_2']
            session_token_1 = self.PROPERTIES['PATHS']['PATH_OS'] + 'src/resources/session-token-1'
            # session_token_2 = self.PROPERTIES['PATHS']['PATH_OS'] + 'src/resources/session-token-2'
            instaloader_1 = Instaloader()
            instaloader_1.load_session_from_file(user_1, session_token_1)
            # instaloader_2 = Instaloader()
            # instaloader_2.load_session_from_file(user_2, session_token_2)
            return iter([instaloader_1])

        self.INSTALOADERS = loaders_init()
        self.CURRENT_LOADER = None
        self.LOADER_WITHOUT_LOGIN = Instaloader()
        self.CURRENT_PROFILE = None
        self.PROFILES_CACHE = {}
        self.CURRENT_STORY = None
        self.SERVICE = SERVICE
        self.LOCK = Event()

    async def search_profile(self, username: str, message: Message) -> ProfileResponse:
        event = Event()
        try:
            status_bar = message.text

            # def search(event_stop: Event):
            # self.download_status_bar(message, status_bar, 'Поиск аккаунта', event_stop)
            await self.ASYNC_BOT.edit_message_text(status_bar + '\nПоиск аккаунта', message.chat.id, message.message_id)
            self.CURRENT_PROFILE = Profile.from_username(self.LOADER_WITHOUT_LOGIN.context, username)
            self.PROFILES_CACHE[self.CURRENT_PROFILE.username] = self.CURRENT_PROFILE
            self.SERVICE.add_profile(message.chat.id, self.CURRENT_PROFILE.username)
            # self.thread_handler(search, event)

            status_bar += '\n✅ Аккаунт найден'
            await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            return await self.profile_data(message, status_bar)
        except ProfileNotExistsException:
            event.set()
            time.sleep(0.1)
            status_bar = message.text + '\n❌ Поиск аккаунта'
            await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            text_message = f'Аккаунта "{username}" нет в инстаграм'
            return ProfileResponse('error', text_message)

    async def profile_data(self, message: Message, status_bar: str) -> ProfileResponse:
        type_response: str
        text_message: str

        if self.CURRENT_PROFILE.is_private:
            type_response = 'private'
            text_message = create_profile_text(self.CURRENT_PROFILE)
        else:
            # async def search(event_stop: Event):
            #     self.download_status_bar(message, status_bar, 'Проверка сторис', event_stop)
            await self.ASYNC_BOT.edit_message_text(status_bar + '\nПроверка сторис', message.chat.id, message.message_id)
            self.CURRENT_LOADER = next(self.INSTALOADERS, None)
            if self.CURRENT_LOADER:
                def try_get_stores():
                    try:
                        self.CURRENT_STORY = next(self.CURRENT_LOADER.get_stories([self.CURRENT_PROFILE.userid]), None)
                    except Exception as exception:
                        text = create_text_insta_error(message, self.CURRENT_LOADER.context.username, exception)
                        self.ASYNC_BOT.send_message(self.PROPERTIES['TELEGRAM']['ADMIN_ID'], text)

                        loaders_modify = list(self.INSTALOADERS)
                        loaders_modify.remove(self.CURRENT_LOADER)
                        self.INSTALOADERS = iter(loaders_modify)
                        self.CURRENT_LOADER = next(self.INSTALOADERS, None)

                        if self.CURRENT_LOADER: try_get_stores()
                try_get_stores()
            # self.thread_handler(search, Event())

            if not self.CURRENT_LOADER:
                text_for_admin = f'Все инста-аккаунты обосрались во время запроса {message.from_user.first_name}'
                await self.ASYNC_BOT.send_message(self.PROPERTIES['TELEGRAM']['ADMIN_ID'], text=text_for_admin)
                status_bar += '\n❌ Информация о сторис'
                await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                text_message = '❌ В данный момент нет ответа от instagram, попробуй сделать запрос позже — через 15-20 минут.'
                return ProfileResponse('error', text_message)


            type_response = 'no_stories' if not self.CURRENT_STORY else 'has_stories'
            text_message = create_profile_text(self.CURRENT_PROFILE, self.CURRENT_STORY)

            status_bar += '\n✅ Информация о сторис'
            await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        # event = Event()
        # self.download_status_bar(message, status_bar, 'Поиск фото', event)
        await self.ASYNC_BOT.edit_message_text(status_bar + '\nПоиск фото', message.chat.id, message.message_id)
        resp = self.LOADER_WITHOUT_LOGIN.context.get_raw(str(self.CURRENT_PROFILE.profile_pic_url))
        # event.set()
        # time.sleep(0.1)
        status_bar += '\n✅ Фото профиля'
        await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        folder_avatar = f"{self.PROPERTIES['PATHS']['PATH_OS']}cache/{self.CURRENT_PROFILE.username}/avatar"
        if not os.path.exists(folder_avatar):
            os.makedirs(folder_avatar)
        date_avatar = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
        filename = date_avatar.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
        avatar_path = os.path.join(folder_avatar, filename)

        if not os.path.exists(avatar_path):
            self.LOADER_WITHOUT_LOGIN.context.write_raw(resp, avatar_path)
            print()

        return ProfileResponse(type_response, text_message, avatar_path, self.CURRENT_PROFILE.username)

    async def download_stories(self, username: str, message: Message, time_created: str) -> StoryResponseInstaloader:
        status_bar = message.text
        if (not self.CURRENT_PROFILE or self.CURRENT_PROFILE.username != username
                or not self.CURRENT_STORY or int(time.time()) - int(time_created) > 600):

            if not self.CURRENT_PROFILE or self.CURRENT_PROFILE.username != username:
                self.CURRENT_PROFILE = self.PROFILES_CACHE.get(username)

                if not self.CURRENT_PROFILE:
                    # async def search(event_stop: Event):
                    # self.download_status_bar(message, status_bar, 'Поиск аккаунта', event_stop, count_idents=2)
                    await self.ASYNC_BOT.edit_message_text(status_bar + '\n\nПоиск аккаунта',
                                                           message.chat.id, message.message_id)
                    self.CURRENT_PROFILE = Profile.from_username(self.LOADER_WITHOUT_LOGIN.context, username)
                    self.PROFILES_CACHE[self.CURRENT_PROFILE.username] = self.CURRENT_PROFILE
                    # self.thread_handler(search, Event())

                    status_bar += '\n\n✅ Аккаунт найден'
                    await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

            # count_idents = 1 if 'Аккаунт найден' in status_bar else 2
            idents = '\n' * 1 if 'Аккаунт найден' in status_bar else '\n' * 2
            # async def search(event_stop: Event):
                # self.download_status_bar(message, status_bar, 'Поиск сторис', event_stop, count_idents=count_idents)
            await self.ASYNC_BOT.edit_message_text(status_bar + f'{idents}Поиск сторис', message.chat.id, message.message_id)
            self.CURRENT_LOADER = next(self.INSTALOADERS, None)
            if self.CURRENT_LOADER:
                def try_get_stores():
                    try:
                        self.CURRENT_STORY = next(self.CURRENT_LOADER.get_stories([self.CURRENT_PROFILE.userid]), None)
                    except Exception as exception:
                        text = create_text_insta_error(message, self.CURRENT_LOADER.context.username, exception)
                        self.ASYNC_BOT.send_message(self.PROPERTIES['TELEGRAM']['ADMIN_ID'], text)

                        loaders_modify = list(self.INSTALOADERS)
                        loaders_modify.remove(self.CURRENT_LOADER)
                        self.INSTALOADERS = iter(loaders_modify)
                        self.CURRENT_LOADER = next(self.INSTALOADERS, None)

                        if self.CURRENT_LOADER: try_get_stores()
                try_get_stores()
            # self.thread_handler(search, Event())


            if self.CURRENT_LOADER and self.CURRENT_STORY:
                status_bar += f'{idents}✅ Сторис найдены'
                await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            else:
                status_bar += f'{idents}❌ Сторис не найдены'
                await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                if not self.CURRENT_LOADER:
                    text_for_admin = f'Все инста-аккаунты обосрались во время запроса {message}'
                    await self.ASYNC_BOT.send_message(self.PROPERTIES['TELEGRAM']['ADMIN_ID'], text=text_for_admin)
                    return StoryResponseInstaloader('error_loader')
                if not self.CURRENT_STORY:
                    return StoryResponseInstaloader('no_stories', self.CURRENT_PROFILE.full_name)

        folder_stories = f"{self.PROPERTIES['PATHS']['PATH_OS']}cache/{self.CURRENT_PROFILE.username}/stories"
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

        count_downloads = 0

        if count_viewed > 0:
            status_bar += (f'\n\nАктуальных сторис: {self.CURRENT_STORY.itemcount}'
                           f'\nСкачано ранее: {count_viewed}')
        if story_data_array:
            status_bar += f'\n\nЗагружено: [{count_downloads}/{len(story_data_array)}]'
        await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        for story_data in story_data_array:
            resp = self.LOADER_WITHOUT_LOGIN.context.get_raw(story_data.url)
            self.LOADER_WITHOUT_LOGIN.context.write_raw(resp, story_data.path)
            print()
            status_bar = status_bar.replace(f'[{count_downloads}/{len(story_data_array)}]',
                                            f'[{count_downloads + 1}/{len(story_data_array)}]')
            await self.ASYNC_BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            count_downloads += 1

        response = StoryResponseInstaloader('has_stories', self.CURRENT_PROFILE.full_name, story_data_array,
                                            self.CURRENT_STORY.itemcount, count_viewed, folder_stories)
        self.CURRENT_STORY = None
        return response


    # def download_status_bar(self, message: Message, status_bar: str, text_search: str,
    #                         event_stop: Event, count_idents: int = 1):
    #     smiles = ['◽', '◾']
    #     idents = '\n' * count_idents
    #
    #     smile_cycle = itertools.cycle(smiles)
    #
    #     async def await_load(event: Event):
    #         while not event.is_set():
    #             text = f'{status_bar}{idents}{next(smile_cycle)} {text_search}'
    #             await self.ASYNC_BOT.edit_message_text(text, message.chat.id, message.message_id)
    #             await asyncio.sleep(0.4)
    #     # await await_load(event_stop)
    #     EXECUTOR.submit(lambda: await_load(event_stop))
    #
    #
    # def thread_handler(self, func, event_stop: Event):
    #     func(event_stop)
    #     event_stop.set()
    #     time.sleep(0.1)