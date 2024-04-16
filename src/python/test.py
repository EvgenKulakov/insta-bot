import configparser
import os
import threading
import time
import itertools
import telebot
import sqlite3
import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])

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
        stop_search = False
        smiles = ['◽', '◾']

        smile_cycle = itertools.cycle(smiles)
        text_load = f'{next(smile_cycle)} Поиск аккаунта'
        current_message = BOT.send_message(message.chat.id, text=text_load)

        def await_load():
            while not stop_search:
                text = next(smile_cycle) + text_load[1:]
                BOT.edit_message_text(text, current_message.chat.id, current_message.message_id)
                time.sleep(0.4)

        # t = threading.Thread(target=await_load)
        # t.start()
        executor.submit(await_load)

        time.sleep(13)
        stop_search = True
        time.sleep(0.1)
        BOT.edit_message_text('✅ Аккаунт найден', current_message.chat.id, current_message.message_id)

    decor(test_multy_treading, message)

def decor(func, message):
    print('before')
    func(message)
    print('after')


BOT.polling(none_stop=True)