import configparser
import os
import threading
import time
import itertools
import random
import requests
import telebot
import sqlite3
import concurrent.futures
import asyncio
from concurrent.futures import ThreadPoolExecutor
from instaloader import Instaloader
from lock_context_wrappers import ProxyContext
from utils import create_text_menu
from database_service import Service
from telebot import types
from instaloader_iterator import InstaloaderIterator


properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

# BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
SERVICE = Service(properties)
executor = ThreadPoolExecutor()

event = threading.Event()

# user_1 = properties['INSTAGRAM']['USER_1']
# user_2 = properties['INSTAGRAM']['USER_1']
# session_token_1 = properties['PATHS']['PATH_OS'] + 'src/resources/session-token-1'
# session_token_2 = properties['PATHS']['PATH_OS'] + 'src/resources/session-token-1'
# instaloader_1 = Instaloader()
# instaloader_1.load_session_from_file(user_1, session_token_1)
# instaloader_2 = Instaloader()
# instaloader_2.load_session_from_file(user_2, session_token_2)
# insta_iter = InstaloaderIterator([instaloader_1, instaloader_2])

# def test_cycle():
#
#     loader1 = next(insta_iter)
#     print(str(loader1) + 'loader1')
#
#     loader2 = next(insta_iter)
#     print(str(loader2) + 'loader2')
#
#     loader3 = next(insta_iter)
#     print(str(loader3) + 'loader3')
#
#     insta_iter.remove(loader2)
#
#     loader1 = next(insta_iter)
#     print(str(loader1) + 'loader1')
#
#     insta_iter.remove(loader1)
#
#     loader = next(insta_iter)
#     print(str(loader) + 'loader empty')
#
#     print('******')
# def test_cycle2():
#
#     loader1 = next(insta_iter)
#     print(str(loader1) + 'loader1')
#
#     loader2 = next(insta_iter)
#     print(str(loader2) + 'loader2')
#
#     loader3 = next(insta_iter)
#     print(str(loader3) + 'loader3')
#
#     insta_iter.add(instaloader_1)
#
#     loader1 = next(insta_iter)
#     print(str(loader1) + 'loader1')
#
#     insta_iter.add(instaloader_2)
#
#     loader = next(insta_iter)
#     print(str(loader) + 'loader empty')
#
#     print('******')

# @BOT.message_handler(commands=['menu'])
# def show_menu(message):
#     mode = 'query'
#     markup = get_menu_markup(message, mode)
#
#     if markup:
#         text = create_text_menu(mode)
#         BOT.send_message(message.chat.id, text=text, reply_markup=markup, parse_mode='HTML')
#     else:
#         BOT.send_message(message.chat.id, text='🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос')
#
#
# @BOT.callback_query_handler(func=lambda call: call.data.startswith('mode'))
# def change_mode(callback_query):
#     mode = callback_query.data.split('|')[1]
#
#     if mode == 'query': mode = 'analyzeNew'
#     elif mode == 'analyzeNew': mode = 'remove'
#     elif mode == 'remove': mode = 'query'
#
#     markup = get_menu_markup(callback_query.message, mode)
#
#     if markup:
#         text = create_text_menu(mode)
#         BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
#                               parse_mode='HTML', reply_markup=markup)
#     else:
#         text = '🧐 Здесь будет меню, когда ты сделаешь хотя бы 1 запрос'
#         BOT.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id)
#
#
# @BOT.message_handler()
# def read_message(message):
#     def test_db():
#         conn = sqlite3.connect('data/stories.db')
#         cursor = conn.cursor()
#
#         cursor.execute("INSERT INTO viewed_stories (username, file_name) VALUES (?, ?)", ('evg', message.text))
#         cursor.execute("SELECT * FROM viewed_stories")
#         conn.commit()
#
#         rows = cursor.fetchall()
#         for row in rows:
#             BOT.send_message(message.chat.id, text=str(row))
#         cursor.close()
#         conn.close()
#     def test_filesystem():
#         folder = 'cache'
#         filename = message.text + '.txt'
#         path = os.path.join(folder, filename)
#
#         if not os.path.isfile(path):
#             os.mknod(path)
#
#         for file_name in os.listdir(folder):
#             BOT.send_message(message.chat.id, text=file_name)
#     def test_multy_treading(message):
#         start = time.time()
#         print('start ' + message.text)
#         stop_search = threading.Event()
#         smiles = ['◽', '◾']
#
#         smile_cycle = itertools.cycle(smiles)
#         text_load = f'{next(smile_cycle)} Поиск аккаунта'
#         current_message = BOT.send_message(message.chat.id, text=text_load)
#
#         def await_load(stop_search):
#             num = 0
#             while not stop_search.is_set():
#                 # text = next(smile_cycle) + text_load[1:]
#                 num += 1
#                 BOT.edit_message_text(str(num), current_message.chat.id, current_message.message_id)
#                 time.sleep(0.5)
#
#         def load(stop_search, await_load):
#             executor.submit(lambda: await_load(stop_search))
#             time.sleep(13)
#             stop_search.set()
#             time.sleep(0.1)
#             BOT.edit_message_text('✅ Аккаунт найден', current_message.chat.id, current_message.message_id)
#             print(time.time() - start)
#         executor.submit(lambda: load(stop_search, await_load))
#     def test_instaloader(message):
#         instaloader_1 = Instaloader()
#         instaloader_1.load_session_from_file(properties['INSTAGRAM']['USER_1'],
#                                              properties['PATHS']['PATH_OS'] + 'src/resources/session-token-1')
#         text = instaloader_1.context.username
#         for k, v, in vars(instaloader_1.context).items():
#             text += f'key: {k}, val: {v}\n'
#         BOT.send_message(message.chat.id, text)
#     def test_exeption(message):
#         try:
#             num = 8/0
#             print(num)
#         except Exception as ex:
#             print(type(ex))
#             text = f'hello\n{ex}'
#             BOT.send_message(message.chat.id, text)
#     def test_async(message):
#
#         def while_test():
#             for n in range(0, 100):
#                 print(str(n) + message.text)
#                 time.sleep(0.5)
#         executor.submit(while_test)
#
#         for num in range(0, 100):
#             print(str(num) + message.text + 'main')
#             time.sleep(0.5)

def get_menu_markup(message, mode: str, usernames = None):
    if not usernames:
        usernames = SERVICE.get_history(message.chat.id)

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
def test_proxy():
    proxy_url = properties['PROXY']['PROXY_URL']

    with ProxyContext(proxy_url):
        response = requests.get('https://api.ipify.org?format=json')
        if response.status_code == 200:
            data = response.json()
            ip_address = data.get('ip')
            print("IP адрес:", ip_address)
        else:
            print("Ошибка при получении IP адреса:", response.status_code)

    response = requests.get('https://api.ipify.org?format=json')
    if response.status_code == 200:
        data = response.json()
        ip_address = data.get('ip')
        print("IP адрес:", ip_address)
    else:
        print("Ошибка при получении IP адреса:", response.status_code)

def test_random():
    for _ in range(0, 10):
        proxy_bool = random.random() < 4 / 5
        print(proxy_bool)

test_random()

# BOT.polling(none_stop=True)