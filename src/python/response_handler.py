from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dtos import ProfileResponse, StoryResponseInstaloader
import time
from threading import Event
from utils import delete_stories_handler


class ResponseHandler:
    BOT: TeleBot
    LOCK: Event
    ADMIN_ID: int
    def __init__(self, BOT: TeleBot, LOCK: Event, ADMIN_ID: int):
        self.BOT = BOT
        self.LOCK = LOCK
        self.ADMIN_ID = ADMIN_ID

    def query_handler(self, response: ProfileResponse, message: Message, loader_name: str | None = None):
        if response.type == 'private':
            with open(response.avatar_path, 'rb') as photo:
                self.BOT.send_photo(message.chat.id, photo, caption=response.text_message, parse_mode='HTML')
        if response.type == 'no_stories':
            markup = InlineKeyboardMarkup()
            text_data = f'query|{response.username}'
            markup.add(InlineKeyboardButton(text='🔍 Сделать новый запрос', callback_data=text_data))
            with open(response.avatar_path, 'rb') as photo:
                self.BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                               parse_mode='HTML', reply_markup=markup)
        if response.type == 'has_stories':
            markup = InlineKeyboardMarkup()
            text_data = f'analyze|{response.username}|{int(time.time())}'
            markup.add(InlineKeyboardButton(text='🐝 Прошерстить', callback_data=text_data))
            with open(response.avatar_path, 'rb') as photo:
                self.BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                               parse_mode='HTML', reply_markup=markup)
        if response.type == 'error':
            self.BOT.send_message(message.chat.id, text=response.text_message)
        if response.type != 'error':
            text_for_admin = f'✅ Успешный поиск профиля у {message.chat.first_name} с помощью аккаунта {loader_name}'
            self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)

        self.LOCK.clear()

    def hornet_handler(self, response: StoryResponseInstaloader, message: Message,
                       loader_name: str | None = None, login_bool: bool | None = None):
        text_message: str
        if response.type == 'has_stories':
            for story_data in response.story_data_array:
                if story_data.content == 'photo':
                    with open(story_data.path, 'rb') as photo:
                        self.BOT.send_photo(message.chat.id, photo)
                if story_data.content == 'video':
                    with open(story_data.path, 'rb') as video:
                        self.BOT.send_video(message.chat.id, video)

            delete_stories_handler(response.story_data_array, response.folder_stories)

            if not response.story_data_array:
                if response.count_stories == 1:
                    text_message = (f'<code>Инсташершень:</code>\n\n'
                                    f'У <b>{response.full_name}</b> сейчас одна актуальная сторис.\n'
                                    f'Я тебе уже отправлял эту сторис - попробуй прошерстить этот аккаунт позже')
                else:
                    text_message = (f'<code>Инсташершень:</code>\n\n'
                                    f'У <b>{response.full_name}</b> {response.count_stories} актуальных сторис.\n'
                                    f'Я тебе уже отправлял все эти сторис - попробуй прошерстить этот аккаунт позже')
            elif response.count_viewed > 0:
                text_message = (f'<code>Инсташершень:</code>\n\n'
                                f'У <b>{response.full_name}</b> {response.count_stories} актуальных сторис.\n'
                                f'Я тебе отправил всего {len(response.story_data_array)} сторис, '
                                f'т.к. другие я тебе отправлял ранее')
            else:
                text_message = (f'<code>Инсташершень:</code>\n\n'
                                f'Все актуальные сторис <b>{response.full_name}</b> отправлены')
            self.BOT.send_message(message.chat.id, text=text_message, parse_mode='HTML')
        if response.type == 'no_stories':
            text_message = (f'<code>Инсташершень:</code>\n\n'
                            f'У <b>{response.full_name}</b> сейчас нет актуальных сторис, попробуй прошерстить его позже')
            self.BOT.send_message(message.chat.id, text=text_message, parse_mode='HTML')
        if response.type == 'error_loader':
            text_message = '❌ В данный момент нет ответа от Instagram, попробуй сделать запрос позже — через 15-20 минут.'
            self.BOT.send_message(message.chat.id, text_message)

        if response.callback_type == 'analyze':
            markup = InlineKeyboardMarkup(row_width=2)
            btn1 = InlineKeyboardButton(text='🔍 Новый запрос', callback_data=f'query|{response.username}')
            btn2 = InlineKeyboardButton(text='🐝 Прошерстить',
                                              callback_data=f'analyzeNew|{response.username}|{int(time.time())}')
            markup.add(btn1, btn2)
            self.BOT.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=markup
            )

        if response.type != 'error_loader':
            text_for_admin = (f'✅ Успешный поиск сторис у {message.chat.first_name} с помощью аккаунта {loader_name}, '
                              f'login_bool:{login_bool}')
            self.BOT.send_message(self.ADMIN_ID, text=text_for_admin)

        self.LOCK.clear()