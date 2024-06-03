import os
import requests
from instaloader import Instaloader, Profile, ProfileNotExistsException, Story
from threading import Lock
from database_service import Service
from dtos import ProfileDTO


class InstaloaderWrapper:
    INSTALOADER: Instaloader
    INSTALOADER_WITHOUT_LOGIN: Instaloader
    SERVICE: Service
    LOCK: Lock

    def __init__(self, instaloader: Instaloader, instaloader_without_login: Instaloader, service: Service):
        self.INSTALOADER = instaloader
        self.INSTALOADER_WITHOUT_LOGIN = instaloader_without_login
        self.SERVICE = service
        self.LOCK = Lock()

    def profile_from_username(self, username: str, telegram_id: int) -> Profile | None:
        with self.LOCK:
            profileDTO = self.SERVICE.get_profile_cache(username)
            if profileDTO:
                if profileDTO.success == 'success':
                    profile = Profile(self.INSTALOADER.context, {'username': username})
                    self.SERVICE.add_history(telegram_id, username)
                    self.SERVICE.add_profile_in_cache(profile.username, profile.full_name, profile.userid)
                    return profile
                if profileDTO.success == 'fail':
                    return None
            else:
                try:
                    profile = Profile.from_username(self.INSTALOADER.context, username)
                    self.SERVICE.add_history(telegram_id, username)
                    self.SERVICE.add_profile_in_cache(profile.username, profile.full_name, profile.userid)
                    return profile
                except ProfileNotExistsException:
                    self.SERVICE.add_fail_in_cache(username)
                    return None


    def get_profile_cache(self, username: str) -> ProfileDTO | None:
        with self.LOCK:
            profileDTO = self.SERVICE.get_profile_cache(username)
            return profileDTO


    def loader_get_stories(self, userid: int) -> Story | None:
        with self.LOCK:
            story = next(self.INSTALOADER.get_stories([userid]), None)
            return story


    def get_raw_dynamic_proxy(self, url: str):
        with self.LOCK:
            return self.INSTALOADER_WITHOUT_LOGIN.context.get_raw(url)


    def write_raw_dynamic_proxy(self, resp: requests.Request, path: str):
        with self.LOCK:
            self.INSTALOADER_WITHOUT_LOGIN.context.write_raw(resp, path)


    def get_raw_login(self, url: str):
        with self.LOCK:
            return self.INSTALOADER.context.get_raw(url)


    def write_raw_login(self, resp: requests.Request, path: str):
        with self.LOCK:
            self.INSTALOADER.context.write_raw(resp, path)


    def get_loader_username(self):
        with self.LOCK:
            return self.INSTALOADER.context.username


class ProxyContext:
    def __init__(self, proxy):
        self.proxy = proxy

    def __enter__(self):
        self.old_http_proxy = os.environ.get('HTTP_PROXY', None)
        self.old_https_proxy = os.environ.get('HTTPS_PROXY', None)
        os.environ['HTTP_PROXY'] = self.proxy
        os.environ['HTTPS_PROXY'] = self.proxy

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old_http_proxy is not None:
            os.environ['HTTP_PROXY'] = self.old_http_proxy
        else:
            del os.environ['HTTP_PROXY']

        if self.old_https_proxy is not None:
            os.environ['HTTPS_PROXY'] = self.old_https_proxy
        else:
            del os.environ['HTTPS_PROXY']