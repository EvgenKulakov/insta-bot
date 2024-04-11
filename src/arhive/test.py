import configparser
import os

import telebot
import sqlite3

properties = configparser.ConfigParser()
properties.read('src/resources/application.properties')

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

    test_filesystem()


BOT.polling(none_stop=True)