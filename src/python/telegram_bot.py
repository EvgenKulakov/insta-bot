import telebot
from telebot import types
import configparser
import insta_loader
from utils import valid_username

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
LOADER = insta_loader.Loader(properties)


@BOT.message_handler(commands=['start'])
def read_start(message):
    BOT.send_message(message.chat.id, text='hello')


@BOT.message_handler()
def read_message(message):
    username = message.text.lower().strip()
    if valid_username(username):
        response = LOADER.set_profile_from_username(username)
        if response.type == 'private':
            photo = open(response.avatar_path, 'rb')
            BOT.send_photo(message.chat.id, photo, caption=response.text_message, parse_mode='HTML')
        if response.type == 'no_stories':
            photo = open(response.avatar_path, 'rb')
            markup = types.InlineKeyboardMarkup()
            text_data = f'query_{LOADER.PROFILE.userid}'
            markup.add(types.InlineKeyboardButton(text='Сделать новый запрос', callback_data=text_data))
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
        if response.type == 'has_stories':
            photo = open(response.avatar_path, 'rb')
            markup = types.InlineKeyboardMarkup()
            text_data = f'analyze_{LOADER.PROFILE.userid}'
            markup.add(types.InlineKeyboardButton(text='Прошерстить', callback_data=text_data))
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
        if response.type == 'error':
            BOT.send_message(message.chat.id, text=response.text_message)
    else:
        BOT.send_message(message.chat.id, text=f'❌ "{message.text}" - некорректный nickname')


@BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
def analyze(callback_query):
    profile_id = int(callback_query.data.split('_')[1])
    LOADER.download_stories(profile_id)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
def query(callback_query):
    profile_id = int(callback_query.data.split('_')[1])
    print(profile_id)


BOT.polling(none_stop=True)