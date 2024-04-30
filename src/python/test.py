import configparser
import os
import threading
import time
import itertools


import telebot
import sqlite3
import concurrent.futures
import asyncio
from concurrent.futures import ThreadPoolExecutor
from instaloader import Instaloader

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
executor = ThreadPoolExecutor()

event = threading.Event()

@BOT.message_handler()
def read_message(message):
    def test_db():
        conn = sqlite3.connect('data/stories.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO viewed_stories (username, file_name) VALUES (?, ?)", ('evg', message.text))
        cursor.execute("SELECT * FROM viewed_stories")
        conn.commit()

        rows = cursor.fetchall()
        for row in rows:
            BOT.send_message(message.chat.id, text=str(row))
        cursor.close()
        conn.close()
    def test_filesystem():
        folder = 'cache'
        filename = message.text + '.txt'
        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            os.mknod(path)

        for file_name in os.listdir(folder):
            BOT.send_message(message.chat.id, text=file_name)
    def test_multy_treading(message):
        start = time.time()
        print('start ' + message.text)
        stop_search = threading.Event()
        smiles = ['◽', '◾']

        if not event.is_set():
            event.set()
            smile_cycle = itertools.cycle(smiles)
            text_load = f'{next(smile_cycle)} Поиск аккаунта'
            current_message = BOT.send_message(message.chat.id, text=text_load)

            def await_load(stop_search):
                num = 0
                while not stop_search.is_set():
                    # text = next(smile_cycle) + text_load[1:]
                    num += 1
                    BOT.edit_message_text(str(num), current_message.chat.id, current_message.message_id)
                    time.sleep(0.5)

            def load(stop_search, await_load):
                executor.submit(lambda: await_load(stop_search))
                time.sleep(13)
                stop_search.set()
                time.sleep(0.1)
                BOT.edit_message_text('✅ Аккаунт найден', current_message.chat.id, current_message.message_id)
                print(time.time() - start)
            future = executor.submit(lambda: load(stop_search, await_load))
            future.result()
            event.clear()
        else:
            print('lock')

    test_multy_treading(message)

    def test_instaloader(message):
        instaloader_1 = Instaloader()
        instaloader_1.load_session_from_file(properties['INSTAGRAM']['USER_1'],
                                             properties['PATHS']['PATH_OS'] + 'src/resources/session-token-1')
        text = instaloader_1.context.username
        for k, v, in vars(instaloader_1.context).items():
            text += f'key: {k}, val: {v}\n'
        BOT.send_message(message.chat.id, text)
    def test_exeption(message):
        try:
            num = 8/0
            print(num)
        except Exception as ex:
            print(type(ex))
            text = f'hello\n{ex}'
            BOT.send_message(message.chat.id, text)
    def test_async(message):

        def while_test():
            for n in range(0, 100):
                print(str(n) + message.text)
                time.sleep(0.5)
        executor.submit(while_test)

        for num in range(0, 100):
            print(str(num) + message.text + 'main')
            time.sleep(0.5)


BOT.polling(none_stop=True)