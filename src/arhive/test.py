import configparser
import time

# import telebot
#
# properties = configparser.ConfigParser()
# properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')
#
# BOT = telebot.TeleBot(properties['TELEGRAM']['BOT'])
#
# @BOT.message_handler()
# def read_message(message):
#     text_message = (f'<code>Инсташершень:</code>\n\n'
#                     f'<blockquote>У <b>Аня Аничкина</b> 5 актуальных сторис, '
#                     f'но я тебе отправил 3 сторис, '
#                     f'т.к. другие я тебе уже отправлял ранее</blockquote>')
#     BOT.send_message(message.chat.id, text=text_message, parse_mode='HTML')
#
#
# BOT.polling(none_stop=True)

t = time.time()
print(int(t))