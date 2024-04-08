from instagrapi import Client
import configparser


properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')


USERNAME = properties['INSTAGRAM']['USER']
PASSWORD = properties['INSTAGRAM']['PASSWORD']

cl = Client()
cl.login(USERNAME, PASSWORD)
cl.dump_settings(properties['INSTAGRAM']['DUMP'])