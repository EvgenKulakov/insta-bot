from instaloader import Instaloader, Profile, ProfileNotExistsException
import os
from datetime import datetime
from data import ProfileResponse
from utils import create_profile_text


class Loader:
    INSTALOADER: Instaloader
    PROFILE: Profile
    def __init__(self, properties):
        user = properties['INSTAGRAM']['USER']
        token = properties['INSTAGRAM']['TOKEN']

        self.INSTALOADER = Instaloader()
        self.INSTALOADER.load_session_from_file(user, token)

    def set_profile_from_username(self, username: str):
        try:
            self.PROFILE = Profile.from_username(self.INSTALOADER.context, username)

            type_response: str
            text_message:str

            if self.PROFILE.is_private:
                type_response = 'private'
                text_message = create_profile_text(self.PROFILE)
            elif not self.PROFILE.has_public_story:
                type_response = 'no_stories'
                text_message = create_profile_text(self.PROFILE)
            else:
                story, *other = self.INSTALOADER.get_stories([self.PROFILE.userid])
                type_response = 'has_stories'
                text_message = create_profile_text(self.PROFILE, story)

            resp = self.INSTALOADER.context.get_raw(str(self.PROFILE.profile_pic_url))

            folder_avatar = f'/home/evgeniy/PycharmProjects/insta-bot/cache/{username}/avatar'
            if not os.path.exists(folder_avatar):
                os.makedirs(folder_avatar)
            date_avatar = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
            filename = date_avatar.strftime("%d-%m-%Y_%H-%M-%S") + '.jpg'
            avatar_path = os.path.join(folder_avatar, filename)

            if not os.path.isfile(avatar_path):
                self.INSTALOADER.context.write_raw(resp, avatar_path)

            return ProfileResponse(type_response, text_message, avatar_path)

        except ProfileNotExistsException:
            text_message = f'❌ Аккаунта "{username}" нет в инстаграм'
            return ProfileResponse('error', text_message)

    def set_profile_from_id(self, profile_id):
        pass

    def download_stories(self, profile_id):
        if self.PROFILE and self.PROFILE.userid == profile_id:
            print('load current profile')
        else:
            print('different id, load new profile')