from instaloader import Instaloader, Profile, ProfileNotExistsException, Story
from telebot import TeleBot
from telebot.types import Message
from configparser import ConfigParser
import os
from datetime import datetime
from dtos import ProfileResponse, StoryResponse
from utils import create_profile_text
from typing import List


class Loader:
    INSTALOADER: Instaloader
    PROFILE: Profile | None
    STORY: Story | None
    BOT: TeleBot
    def __init__(self, properties: ConfigParser, BOT: TeleBot):
        user = properties['INSTAGRAM']['USER']
        session_token = properties['INSTAGRAM']['TOKEN']

        self.INSTALOADER = Instaloader()
        self.INSTALOADER.load_session_from_file(user, session_token)
        self.PROFILE = None
        self.STORY = None
        self.BOT = BOT

    def set_profile_from_username(self, username: str, message: Message) -> ProfileResponse:
        try:
            self.PROFILE = Profile.from_username(self.INSTALOADER.context, username)
            status_bar = message.text + '\n✅ Аккаунт найден'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            return self.profile_data(message, status_bar)
        except ProfileNotExistsException:
            text_message = f'❌ Аккаунта "{username}" нет в инстаграм'
            return ProfileResponse('error', text_message)

    def set_profile_from_id(self, profile_id: int, message: Message) -> ProfileResponse:
        self.PROFILE = Profile.from_id(self.INSTALOADER.context, profile_id)
        status_bar = message.text + '\n✅ Аккаунт найден'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
        return self.profile_data(message, status_bar)

    def profile_data(self, message: Message, status_bar: str) -> ProfileResponse:
        type_response: str
        text_message: str

        if self.PROFILE.is_private:
            type_response = 'private'
            text_message = create_profile_text(self.PROFILE)
        elif not self.PROFILE.has_public_story:
            type_response = 'no_stories'
            text_message = create_profile_text(self.PROFILE)
        else:
            self.STORY = next(self.INSTALOADER.get_stories([self.PROFILE.userid]))
            status_bar += '\n✅ Информация о сторис'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
            type_response = 'has_stories'
            text_message = create_profile_text(self.PROFILE, self.STORY)

        resp = self.INSTALOADER.context.get_raw(str(self.PROFILE.profile_pic_url))
        status_bar += '\n✅ Фото профиля'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        folder_avatar = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{self.PROFILE.username}/avatar'
        if not os.path.exists(folder_avatar):
            os.makedirs(folder_avatar)
        date_avatar = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
        filename = date_avatar.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
        avatar_path = os.path.join(folder_avatar, filename)

        if not os.path.isfile(avatar_path):
            self.INSTALOADER.context.write_raw(resp, avatar_path)

        return ProfileResponse(type_response, text_message, avatar_path)

    def download_stories(self, profile_id: int, message: Message) -> List[StoryResponse] | None:
        status_bar = message.text
        if not self.PROFILE or self.PROFILE.userid != profile_id or not self.STORY:
            if not self.PROFILE or self.PROFILE.userid != profile_id:
                status_bar += '\nПоиск аккаунта'
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

                self.PROFILE = Profile.from_id(self.INSTALOADER.context, profile_id)
                status_bar = status_bar.replace('Поиск аккаунта', '✅ Аккаунт найден')
            status_bar += '\nПоиск сторис'
            self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

            self.STORY = next(self.INSTALOADER.get_stories([profile_id]))
            if self.STORY and self.STORY.itemcount > 0:
                status_bar = status_bar.replace('Поиск сторис', '✅ Сторис найдены')
            else:
                status_bar = status_bar.replace('Поиск сторис', '❌ Сторис не найдены')
                self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                return None

        count_downloads = 0
        status_bar += f'\nЗагружено [{count_downloads}/{self.STORY.itemcount}]'
        self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)

        folder_stories = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{self.PROFILE.username}/stories'
        if not os.path.exists(folder_stories):
            os.makedirs(folder_stories)

        story_dtos = []

        for item in self.STORY.get_items():
            filename = item.date_local.strftime('%d-%m-%Y_%H-%M-%S')
            path = os.path.join(folder_stories, filename)

            if item.is_video:
                if not os.path.isfile(path + '.mp4'):
                    resp = self.INSTALOADER.context.get_raw(str(item.video_url))
                    self.INSTALOADER.context.write_raw(resp, path + '.mp4')
                    story_dtos.append(StoryResponse('video', path + '.mp4'))
                    status_bar = status_bar.replace(f'[{count_downloads}/{self.STORY.itemcount}]',
                                                    f'[{count_downloads + 1}/{self.STORY.itemcount}]')
                    self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                    count_downloads += 1
            else:
                if not os.path.isfile(path + ".jpg"):
                    resp = self.INSTALOADER.context.get_raw(str(item.url))
                    self.INSTALOADER.context.write_raw(resp, path + '.jpg')
                    story_dtos.append(StoryResponse('photo', path + '.jpg'))
                    status_bar = status_bar.replace(f'[{count_downloads}/{self.STORY.itemcount}]',
                                                    f'[{count_downloads + 1}/{self.STORY.itemcount}]')
                    self.BOT.edit_message_text(status_bar, message.chat.id, message.message_id)
                    count_downloads += 1



        self.STORY = None
        return story_dtos