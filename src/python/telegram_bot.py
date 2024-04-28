from typing import List
from telebot import telebot, types
from telebot.types import Message, InlineKeyboardMarkup
import configparser
from instaloader_api import Loader
from utils import valid_username, files_handler, create_text_menu, get_start_text
from dtos import ProfileResponse
import time
from database_service import Service


properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
SERVICE = Service(properties)
LOADERS = {int(properties['TELEGRAM']['ADMIN_ID']): Loader(properties, BOT, SERVICE),
           int(properties['TELEGRAM']['ANNA_ID']): Loader(properties, BOT, SERVICE),
           int(properties['TELEGRAM']['DASHA_ID']): Loader(properties, BOT, SERVICE)}

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
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@BOT.message_handler()
def read_message(message):
    loader = LOADERS.get(message.chat.id)
    if loader:
        username = message.text.lower().strip()
        if valid_username(username):
            status_bar = BOT.send_message(message.chat.id, text='Делаю запрос...')
            response = loader.search_profile(username, status_bar)
            query_handler(response, message)
        else:
            BOT.send_message(message.chat.id, text=f'❌ "{message.text}" - некорректный никнейм')
    else:
        BOT.send_message(message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


@BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
def query(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        status_bar = BOT.send_message(callback_query.message.chat.id, text='Делаю запрос...')
        username = callback_query.data.split('|')[1]
        response = loader.search_profile(username, status_bar)
        query_handler(response, callback_query.message)
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


def query_handler(response: ProfileResponse, message: Message):
    if response.type == 'private':
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message, parse_mode='HTML')
    if response.type == 'no_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'query|{response.username}'
        markup.add(types.InlineKeyboardButton(text='🔍 Сделать новый запрос', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'has_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'analyze|{response.username}|{int(time.time())}'
        markup.add(types.InlineKeyboardButton(text='🐝 Прошерстить', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'error':
        BOT.send_message(message.chat.id, text=response.text_message)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
def analyze(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
        callback_type, username, time_create = callback_query.data.split('|')
        status_bar = BOT.send_message(callback_query.message.chat.id, text='Загружаю сторис...')
        response = loader.download_stories(username, status_bar, time_create)
        text_message: str
        if response:
            for story_data in response.story_data_array:
                if story_data.content == 'photo':
                    with open(story_data.path, 'rb') as photo:
                        BOT.send_photo(callback_query.message.chat.id, photo)
                if story_data.content == 'video':
                    with open(story_data.path, 'rb') as video:
                        BOT.send_video(callback_query.message.chat.id, video)

            files_handler(response.story_data_array, response.folder_stories)

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
            BOT.send_message(callback_query.message.chat.id, text=text_message, parse_mode='HTML')
        else:
            text_message = ('<code>Инсташершень:</code>\n\n'
                            'У данного аккаунта сейчас нет актуальных сторис, попробуй прошерстить его позже')
            BOT.send_message(callback_query.message.chat.id, text=text_message, parse_mode='HTML')

        if callback_type == 'analyze':
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn1 = types.InlineKeyboardButton(text='🔍 Новый запрос', callback_data=f'query|{username}')
            btn2 = types.InlineKeyboardButton(text='🐝 Прошерстить',
                                              callback_data=f'analyzeNew|{username}|{int(time.time())}')
            markup.add(btn1, btn2)
            BOT.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=markup
            )
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@BOT.callback_query_handler(func=lambda call: call.data.startswith('remove'))
def remove_history(callback_query):
    loader = LOADERS.get(callback_query.message.chat.id)
    if loader:
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
    else:
        BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


BOT.polling(none_stop=True)