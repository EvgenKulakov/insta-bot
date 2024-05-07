import os
import requests
from instaloader import Instaloader, Profile, ProfileNotExistsException, Story
from threading import Lock
from database_service import Service


class InstaloaderWrapper:
    INSTALOADER: Instaloader
    INSTALOADER_WITHOUT_LOGIN: Instaloader
    SERVICE: Service
    PROXY: str
    LOCK: Lock

    def __init__(self, instaloader: Instaloader, instaloader_without_login: Instaloader, service: Service, proxy: str):
        self.INSTALOADER = instaloader
        self.INSTALOADER_WITHOUT_LOGIN = instaloader_without_login
        self.SERVICE = service
        self.PROXY = proxy
        self.LOCK = Lock()

    def profile_from_username(self, username: str, telegram_id: int) -> Profile | None:
        with self.LOCK:
            with ProxyContext(self.PROXY):
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


    def loader_get_stories(self, userid: int) -> Story | None:
        with self.LOCK:
            with ProxyContext(self.PROXY):
                story = next(self.INSTALOADER.get_stories([userid]), None)
                return story


    def get_raw_dynamic_proxy(self, url: str, proxy: bool):
        with self.LOCK:
            if proxy:
                with ProxyContext(self.PROXY):
                    return self.INSTALOADER_WITHOUT_LOGIN.context.get_raw(url)
            else:
                return self.INSTALOADER_WITHOUT_LOGIN.context.get_raw(url)


    def write_raw_dynamic_proxy(self, resp: requests.Request, path: str, proxy: bool):
        with self.LOCK:
            if proxy:
                with ProxyContext(self.PROXY):
                    self.INSTALOADER_WITHOUT_LOGIN.context.write_raw(resp, path)
            else:
                self.INSTALOADER_WITHOUT_LOGIN.context.write_raw(resp, path)


    def get_raw_login(self, url: str):
        with self.LOCK:
            with ProxyContext(self.PROXY):
                return self.INSTALOADER.context.get_raw(url)


    def write_raw_login(self, resp: requests.Request, path: str):
        with self.LOCK:
            with ProxyContext(self.PROXY):
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