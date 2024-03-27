import configparser
import os
from typing import Callable
from urllib.parse import urlparse

import instaloader
from instaloader import Profile
from instaloader.instaloader import _PostPathFormatter

properties = configparser.ConfigParser()
properties.read('/home/evgeniy/PycharmProjects/insta-bot/src/resources/application.properties')

def download():
    USER = properties['SECURITY']['USER']
    TOKEN = properties['SECURITY']['TOKEN']
    L = instaloader.Instaloader()
    L.load_session_from_file(USER, TOKEN)

    username = 'samoylovaoxana'
    profile = Profile.from_username(L.context, username)
    L.download_profilepic(profile)
    print(profile.full_name)
    print(profile.has_public_story)
    print(profile.biography)
    print(profile.is_private)

    print('***************************')

    def already_downloaded(path: str) -> bool:
        if not os.path.isfile(path):
            return False
        else:
            L.context.log(path + ' exists', end=' ', flush=True)
            return True

    stories = L.get_stories([profile.userid])

    for story in stories:
        print(story.itemcount)
        print(story.latest_media_local)
        print(dir(story))
        story_items = story.get_items()
        for item in story_items:
            print(dir(item))

            dirname = _PostPathFormatter(item, L.sanitize_paths).format(L.dirname_pattern, target=f'{username}')
            filename_template = os.path.join(dirname, L.format_filename(item, target=f'{username}'))

            if item.is_video:
                filename = prepare_filename(filename_template, lambda: str(item.video_url))
                if not already_downloaded(filename + ".mp4"):
                    L.download_pic(filename=filename, url=str(item.video_url), mtime=item.date_local)
            else:
                filename = prepare_filename(filename_template, lambda: str(item.url))
                if not already_downloaded(filename + ".jpg"):
                    L.download_pic(filename=filename, url=str(item.url), mtime=item.date_local)
        print('****************************************')

    print('*********************************')

    print("Сторис загружены успешно!")

def prepare_filename(filename_template: str, url: Callable[[], str]) -> str:
    if "{filename}" in filename_template:
        filename = filename_template.replace("{filename}",
                                             os.path.splitext(os.path.basename(urlparse(url()).path))[0])
    else:
        filename = filename_template
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename


download()

