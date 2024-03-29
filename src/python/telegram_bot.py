import telebot
from telebot import types
import configparser
import insta_loader

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
LOADER = insta_loader.Loader(properties)


@BOT.message_handler(commands=['start'])
def read_start(message):
    text = "Привет! Это сообщение с картинкой и кнопкой."

    photo = open('/home/evgeniy/PycharmProjects/insta-bot/cache/morgen_shtern/avatar/19-02-2024_12-24-54.jpg', 'rb')

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Прошерстить', callback_data='none'))

    BOT.send_photo(message.chat.id, photo, caption=text, reply_markup=markup)

@BOT.message_handler()
def read_message(message):
    print('validation message.text')
    text_message = LOADER.set_profile_from_username('victoriabonya')
    text_data = f'analyze_{LOADER.PROFILE.userid}'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Прошерстить', callback_data=text_data))
    BOT.send_message(message.chat.id, text=text_message, reply_markup=markup)

@BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
def analyze(callback_query):
    profile_id = int(callback_query.data.split('_')[1])
    LOADER.download_stories(profile_id)

@BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
def query(callback_query):
    profile_id = int(callback_query.data.split('_')[1])


BOT.polling(none_stop=True)