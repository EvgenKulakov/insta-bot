from instaloader import Instaloader, Profile, ProfileNotExistsException, Story
from threading import Lock
from database_service import Service


class InstaloaderWrapper:
    INSTALOADER: Instaloader
    SERVICE: Service
    LOCK: Lock

    def __init__(self, instaloader: Instaloader, service: Service):
        self.INSTALOADER = instaloader
        self.SERVICE = service
        self.LOCK = Lock()

    def profile_from_username(self, username: str, telegram_id: int) -> Profile | None:
        with self.LOCK:
            success_fail = self.SERVICE.get_success_fail(username)
            if success_fail:
                if success_fail.type == 'success':
                    profile = Profile(self.INSTALOADER.context, {'username': username})
                    self.SERVICE.add_profile(telegram_id, username)
                    return profile
                if success_fail.type == 'fail':
                    return None
            else:
                try:
                    profile = Profile.from_username(self.INSTALOADER.context, username)
                    self.SERVICE.add_profile(telegram_id, username)
                    self.SERVICE.add_success_fail(username, 'success')
                    return profile
                except ProfileNotExistsException:
                    self.SERVICE.add_success_fail(username, 'fail')
                    return None


    def get_stories(self, userid: int) -> Story | None:
        with self.LOCK:
            story = next(self.INSTALOADER.get_stories([userid]), None)
            return story


    def get_context(self):
        return self.INSTALOADER.context