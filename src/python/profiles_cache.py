from typing import Dict
from dtos import ProfileDTO
from threading import Lock


class ProfilesCache:
    CACHE: Dict[str, ProfileDTO]
    LOCK: Lock

    def __init__(self):
        self.CACHE = {}
        self.LOCK = Lock()


    def put_profile(self, profileDTO: ProfileDTO | None):
        with self.LOCK:
            if profileDTO:
                self.CACHE[profileDTO.username] = profileDTO


    def get_profile(self, username: str) -> ProfileDTO:
        with self.LOCK:
            return self.CACHE.get(username)