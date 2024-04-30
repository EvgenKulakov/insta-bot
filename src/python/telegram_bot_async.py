import asyncio
from typing import List, Set
from telebot import telebot, types, async_telebot
from telebot.types import Message, InlineKeyboardMarkup
import configparser
from instaloader_api_async import Loader
from utils import valid_username, files_handler, create_text_menu, get_start_text
from dtos import ProfileResponse
import time
from database_service import Service
from concurrent.futures import ThreadPoolExecutor

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

# BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
ASYNC_BOT = async_telebot.AsyncTeleBot(properties['TELEGRAM']['BOT'])
SERVICE = Service(properties)
# EXECUTOR = ThreadPoolExecutor()
LOADER = Loader(properties, ASYNC_BOT, SERVICE)
SECURITY = {int(properties['TELEGRAM']['ADMIN_ID']),
            int(properties['TELEGRAM']['ANNA_ID']),
            int(properties['TELEGRAM']['DASHA_ID'])}
# BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='✅ INSTALOADER start')


@ASYNC_BOT.message_handler(commands=['start'])
async def read_start(message):
    if message.chat.id in SECURITY:
        text = get_start_text()
        await ASYNC_BOT.send_message(message.chat.id, text=text, parse_mode='HTML')
    else:
        await ASYNC_BOT.send_message(message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


@ASYNC_BOT.message_handler(commands=['menu'])
async def show_menu(message):
    if message.chat.id in SECURITY:
        mode = 'query'
        markup = get_menu_markup(message, mode)

        if markup:
            text = create_text_menu(mode)
            await ASYNC_BOT.send_message(message.chat.id, text=text, reply_markup=markup, parse_mode='HTML')
        else:
            await ASYNC_BOT.send_message(message.chat.id, text='🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос')
    else:
        await ASYNC_BOT.send_message(message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


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


@ASYNC_BOT.callback_query_handler(func=lambda call: call.data.startswith('mode'))
async def change_mode(callback_query):
    if callback_query.message.chat.id in SECURITY:
        mode = callback_query.data.split('|')[1]

        if mode == 'query': mode = 'analyzeNew'
        elif mode == 'analyzeNew': mode = 'remove'
        elif mode == 'remove': mode = 'query'

        markup = get_menu_markup(callback_query.message, mode)

        if markup:
            text = create_text_menu(mode)
            await ASYNC_BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                  parse_mode='HTML', reply_markup=markup)
        else:
            text = '🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос'
            await ASYNC_BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id)
    else:
        await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@ASYNC_BOT.message_handler()
async def read_message(message):
    if message.chat.id in SECURITY:
        username = message.text.lower().strip()
        if valid_username(username):
            # if not LOADER.LOCK.is_set():
                # LOADER.LOCK.set()
            if True:
                status_bar = await ASYNC_BOT.send_message(message.chat.id, text='Делаю запрос...')
                # future = EXECUTOR.submit(lambda: LOADER.search_profile(username, status_bar))
                # response = future.result()
                response = await LOADER.search_profile(username, status_bar)
                await query_handler(response, message)
                # LOADER.LOCK.clear()
            else:
                text = 'Я сейчас делаю другой запрос, обожди буквально 30 секунд и попробуй ещё раз'
                await ASYNC_BOT.send_message(message.chat.id, text=text)
        else:
            await ASYNC_BOT.send_message(message.chat.id, text=f'❌ "{message.text}" - некорректный никнейм')
    else:
        await ASYNC_BOT.send_message(message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(message))


@ASYNC_BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
async def query(callback_query):
    if callback_query.message.chat.id in SECURITY:
        status_bar = await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Делаю запрос...')
        username = callback_query.data.split('|')[1]
        response = await LOADER.search_profile(username, status_bar)
        await query_handler(response, callback_query.message)
    else:
        await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


async def query_handler(response: ProfileResponse, message: Message):
    if response.type == 'private':
        with open(response.avatar_path, 'rb') as photo:
            await ASYNC_BOT.send_photo(message.chat.id, photo, caption=response.text_message, parse_mode='HTML')
    if response.type == 'no_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'query|{response.username}'
        markup.add(types.InlineKeyboardButton(text='🔍 Сделать новый запрос', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            await ASYNC_BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'has_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'analyze|{response.username}|{int(time.time())}'
        markup.add(types.InlineKeyboardButton(text='🐝 Прошерстить', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            await ASYNC_BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'error':
        await ASYNC_BOT.send_message(message.chat.id, text=response.text_message)


@ASYNC_BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
async def analyze(callback_query):
    if callback_query.message.chat.id in SECURITY:
        callback_type, username, time_create = callback_query.data.split('|')
        status_bar = await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Загружаю сторис...')
        response = await LOADER.download_stories(username, status_bar, time_create)
        text_message: str
        if response.type == 'has_stories':
            for story_data in response.story_data_array:
                if story_data.content == 'photo':
                    with open(story_data.path, 'rb') as photo:
                        await ASYNC_BOT.send_photo(callback_query.message.chat.id, photo)
                if story_data.content == 'video':
                    with open(story_data.path, 'rb') as video:
                        await ASYNC_BOT.send_video(callback_query.message.chat.id, video)

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
            await ASYNC_BOT.send_message(callback_query.message.chat.id, text=text_message, parse_mode='HTML')
        if response.type == 'no_stories':
            text_message = (f'<code>Инсташершень:</code>\n\n'
                            f'У <b>{response.full_name}</b> сейчас нет актуальных сторис, попробуй прошерстить его позже')
            await ASYNC_BOT.send_message(callback_query.message.chat.id, text=text_message, parse_mode='HTML')
        if response.type == 'error_loader':
            text_message = '❌ В данный момент нет ответа от instagram, попробуй сделать запрос позже — через 15-20 минут.'
            await ASYNC_BOT.send_message(callback_query.message.chat.id, text_message)


        if callback_type == 'analyze':
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn1 = types.InlineKeyboardButton(text='🔍 Новый запрос', callback_data=f'query|{username}')
            btn2 = types.InlineKeyboardButton(text='🐝 Прошерстить',
                                              callback_data=f'analyzeNew|{username}|{int(time.time())}')
            markup.add(btn1, btn2)
            await ASYNC_BOT.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=markup
            )
    else:
        await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


@ASYNC_BOT.callback_query_handler(func=lambda call: call.data.startswith('remove'))
async def remove_history(callback_query):
    if callback_query.message.chat.id in SECURITY:
        telegram_id = callback_query.message.chat.id
        mode, username, time_created = callback_query.data.split('|')
        refresh_usernames = SERVICE.remove_profile(telegram_id, username)
        markup = get_menu_markup(callback_query.message, mode, refresh_usernames)

        if markup:
            text = create_text_menu(mode)
            await ASYNC_BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=markup)
        else:
            text = '🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос'
            await ASYNC_BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id)
    else:
        await ASYNC_BOT.send_message(callback_query.message.chat.id, text='Нет доступа')
        await ASYNC_BOT.send_message(properties['TELEGRAM']['ADMIN_ID'], text='Левый пользователь. Лог:\n\n' + str(callback_query.message))


asyncio.run(ASYNC_BOT.polling())