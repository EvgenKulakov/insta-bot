from instaloader import Instaloader, Profile, ProfileNotExistsException, Story


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
            story, *other = self.INSTALOADER.get_stories([self.PROFILE.userid])
            text = 'success\n'
            text += self.PROFILE.full_name + '\n'
            text += str(self.PROFILE.has_public_story) + '\n'
            text += self.PROFILE.biography + '\n'
            text += str(self.PROFILE.is_private) + '\n'
            text += str(story.itemcount) + '\n'
            text += str(story.latest_media_local) + '\n'
            return text
        except ProfileNotExistsException:
            return f'error user {username} не найден'

    def set_profile_from_id(self, profile_id):
        pass

    def download_stories(self, profile_id):
        if self.PROFILE and self.PROFILE.userid == profile_id:
            print('load current profile')
        else:
            print('different id, load new profile')