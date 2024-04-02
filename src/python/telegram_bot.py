from telebot import telebot, types
from telebot.types import Message
import configparser
import insta_loader
from utils import valid_username
from dtos import ProfileResponse

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
LOADER = insta_loader.Loader(properties, BOT)


@BOT.message_handler(commands=['start'])
def read_start(message):
    BOT.send_message(message.chat.id, text='hello')


@BOT.message_handler()
def read_message(message):
    username = message.text.lower().strip()
    if valid_username(username):
        status_bar = BOT.send_message(message.chat.id, text='Делаю запрос...')
        response = LOADER.set_profile_from_username(username, status_bar)
        query_handler(response, message)
    else:
        BOT.send_message(message.chat.id, text=f'❌ "{message.text}" - некорректный никнейм')


@BOT.callback_query_handler(func=lambda call: call.data.startswith('query'))
def query(callback_query):
    status_bar = BOT.send_message(callback_query.message.chat.id, text='Делаю запрос...')
    profile_id = int(callback_query.data.split('_')[1])
    response = LOADER.set_profile_from_id(profile_id, status_bar)
    query_handler(response, callback_query.message)


def query_handler(response: ProfileResponse, message: Message):
    if response.type == 'private':
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message, parse_mode='HTML')
    if response.type == 'no_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'query_{LOADER.PROFILE.userid}'
        markup.add(types.InlineKeyboardButton(text='Сделать новый запрос', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'has_stories':
        markup = types.InlineKeyboardMarkup()
        text_data = f'analyze_{LOADER.PROFILE.userid}'
        markup.add(types.InlineKeyboardButton(text='Прошерстить', callback_data=text_data))
        with open(response.avatar_path, 'rb') as photo:
            BOT.send_photo(message.chat.id, photo, caption=response.text_message,
                           parse_mode='HTML', reply_markup=markup)
    if response.type == 'error':
        BOT.send_message(message.chat.id, text=response.text_message)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('analyze'))
def analyze(callback_query):
    profile_id = int(callback_query.data.split('_')[1])
    status_bar = BOT.send_message(callback_query.message.chat.id, text='Загружаю сторис...')
    response = LOADER.download_stories(profile_id, status_bar)
    text_message: str
    if response:
        for story_data in response.story_data_array:
            if story_data.content == 'photo':
                with open(story_data.path, 'rb') as photo:
                    BOT.send_photo(callback_query.message.chat.id, photo)
            if story_data.content == 'video':
                with open(story_data.path, 'rb') as video:
                    BOT.send_video(callback_query.message.chat.id, video)

        for story_data in response.story_data_array:
            print(f'обнуление {story_data.path}')

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

    if callback_query.data.split('_')[0] == 'analyze':
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(text='Новый запрос', callback_data=f'query_{profile_id}')
        btn2 = types.InlineKeyboardButton(text='Прошерстить', callback_data=f'analyzeNew_{profile_id}')
        markup.add(btn1, btn2)
        BOT.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=markup
        )


BOT.polling(none_stop=True)