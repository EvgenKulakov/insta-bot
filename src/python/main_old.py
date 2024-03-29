import configparser
import os
from datetime import datetime
from typing import Callable
from urllib.parse import urlparse

import instaloader
from instaloader import Profile
from instaloader.instaloader import _PostPathFormatter

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

def download():
    USER = properties['INSTAGRAM']['USER']
    TOKEN = properties['INSTAGRAM']['TOKEN']
    L = instaloader.Instaloader()
    L.load_session_from_file(USER, TOKEN)

    username = 'morgen_shtern'
    profile = Profile.from_username(L.context, username)

    target_folder_pic = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{username}/avatar'
    if not os.path.exists(target_folder_pic):
        os.makedirs(target_folder_pic)

    resp = L.context.get_raw(str(profile.profile_pic_url))
    date_pic = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
    filename_pic = date_pic.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
    path_pic = os.path.join(target_folder_pic, filename_pic)

    if not os.path.isfile(path_pic):
        L.context.write_raw(resp, path_pic)

    print(profile.full_name)
    print(profile.has_public_story)
    print(profile.biography)
    print(profile.is_private)

    print('***************************')

    stories = L.get_stories([profile.userid])

    for story in stories:
        target_folder = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{username}/stories'
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        story_items = story.get_items()
        for item in story_items:
            filename = item.date_local.strftime('%d-%m-%Y_%H-%M-%S')
            path = os.path.join(target_folder, filename)

            if item.is_video:
                if not os.path.isfile(path + '.mp4'):
                    resp = L.context.get_raw(str(item.video_url))
                    L.context.write_raw(resp, path + '.mp4')
            else:
                if not os.path.isfile(path + ".jpg"):
                    resp = L.context.get_raw(str(item.url))
                    L.context.write_raw(resp, path + '.jpg')

    print("Сторис загружены успешно!")


download()

