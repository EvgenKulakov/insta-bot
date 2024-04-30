from typing import List
from instaloader import Instaloader
from telebot import telebot, types
from telebot.types import Message, InlineKeyboardMarkup
import configparser
from instaloader_api import Loader
from instaloader_iterator import InstaloaderIterator
from utils import valid_username, create_text_menu, get_start_text
import time
from database_service import Service
from concurrent.futures import ThreadPoolExecutor

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

def loaders_init() -> InstaloaderIterator:
    user_1 = properties['INSTAGRAM']['USER_1']
    user_2 = properties['INSTAGRAM']['USER_2']
    session_token_1 = properties['PATHS']['PATH_OS'] + 'src/resources/session-token-1'
    session_token_2 = properties['PATHS']['PATH_OS'] + 'src/resources/session-token-2'
    instaloader_1 = Instaloader()
    instaloader_1.load_session_from_file(user_1, session_token_1)
    instaloader_2 = Instaloader()
    instaloader_2.load_session_from_file(user_2, session_token_2)
    return InstaloaderIterator([instaloader_1, instaloader_2])

INSTALOADERS = loaders_init()
BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
SERVICE = Service(properties)
EXECUTOR = ThreadPoolExecutor()
LOADERS = {int(properties['TELEGRAM']['ADMIN_ID']): Loader(properties, INSTALOADERS, BOT, SERVICE, EXECUTOR),
           int(properties['TELEGRAM']['ANNA_ID']): Loader(properties, INSTALOADERS, BOT, SERVICE, EXECUTOR),
           int(properties['TELEGRAM']['DASHA_ID']): Loader(properties, INSTALOADERS, BOT, SERVICE, EXECUTOR)}
BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='✅ INSTABOT start')


@BOT.message_handler(commands=['start'])
def read_start(message):
    loader = LOADERS.get(message.chat.id)
    if loader:
        text = get_start_text()
        BOT.send_message(message.chat.id, text=text, parse_mode='HTML')
    else:
        BOT.send_message(message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


@BOT.message_handler(commands=['menu'])
def show_menu(message):
    loader = LOADERS.get(message.chat.id)
    if loader:
        mode = 'query'
        markup = get_menu_markup(message, mode)

        if markup:
            text = create_text_menu(mode)
            BOT.send_message(message.chat.id, text=text, reply_markup=markup, parse_mode='HTML')
        else:
            BOT.send_message(message.chat.id, text='🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос')
    else:
        BOT.send_message(message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


def get_menu_markup(message: Message, mode: str, usernames: List[str] | None = None) -> InlineKeyboardMarkup | None:
    if not usernames:
        usernames = SERVICE.get_profiles(message.chat.id)

    if len(usernames) > 0:
        mode_smiles = {'query': '🔍 ', 'analyzeNew': '🐝 ', 'remove': '❌ '}
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Переключить режим >>", callback_data=f'mode|{mode}'),
        )

        for i in range(0, len(usernames), 2):
            if i + 1 < len(usernames):
                text_data1 = f'{mode}|{usernames[i]}|{int(time.time())}'
                text_data2 = f'{mode}|{usernames[i + 1]}|{int(time.time())}'
                row = [types.InlineKeyboardButton(text=f'{mode_smiles[mode]}{usernames[i]}', callback_data=text_data1),
                       types.InlineKeyboardButton(text=f'{mode_smiles[mode]}{usernames[i + 1]}', callback_data=text_data2)]
                markup.row(*row)
            else:
                text_data = f'{mode}|{usernames[i]}|{int(time.time())}'
                markup.add(types.InlineKeyboardButton(text=f'{mode_smiles[mode]}{usernames[i]}', callback_data=text_data))

        return markup
    else:
        return None


@BOT.callback_query_handler(func=lambda call: call.data.startswith('mode'))
def change_mode(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        if not loader.LOCK.is_set():
            loader.LOCK.set()
            mode = callback_query.data.split('|')[1]

            if mode == 'query': mode = 'analyzeNew'
            elif mode == 'analyzeNew': mode = 'remove'
            elif mode == 'remove': mode = 'query'

            markup = get_menu_markup(callback_query.message, mode)

            if markup:
                text = create_text_menu(mode)
                BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                      parse_mode='HTML', reply_markup=markup)
            else:
                text = '🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос'
                BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id)

            loader.LOCK.clear()
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@BOT.message_handler()
def read_message(message):
    loader = LOADERS.get(message.chat.id)
    if loader:
        username = message.text.lower().strip()
        if valid_username(username):
            if not loader.LOCK.is_set():
                loader.LOCK.set()
                status_bar = BOT.send_message(message.chat.id, text='Делаю запрос...')
                EXECUTOR.submit(lambda: loader.search_profile(username, status_bar))
        else:
            BOT.send_message(message.chat.id, text=f'❌ "{message.text}" - некорректный никнейм')
    else:
        BOT.send_message(message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


@BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
def query(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        if not loader.LOCK.is_set():
            loader.LOCK.set()
            status_bar = BOT.send_message(callback_query.message.chat.id, text='Делаю запрос...')
            username = callback_query.data.split('|')[1]
            EXECUTOR.submit(lambda: loader.search_profile(username, status_bar))
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
def hornet(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        if not loader.LOCK.is_set():
            loader.LOCK.set()
            callback_type, username, time_create = callback_query.data.split('|')
            status_bar = BOT.send_message(callback_query.message.chat.id, text='Загружаю сторис...')
            EXECUTOR.submit(lambda: loader.download_stories(callback_type, username, status_bar,
                                                            callback_query.message, time_create))
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@BOT.callback_query_handler(func=lambda call: call.data.startswith('remove'))
def remove_history(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        if not loader.LOCK.is_set():
            loader.LOCK.set()
            telegram_id = callback_query.message.chat.id
            mode, username, time_created = callback_query.data.split('|')
            refresh_usernames = SERVICE.remove_profile(telegram_id, username)
            markup = get_menu_markup(callback_query.message, mode, refresh_usernames)

            if markup:
                text = create_text_menu(mode)
                BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=markup)
            else:
                text = '🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос'
                BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id)

            loader.LOCK.clear()
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


BOT.polling(none_stop=True)