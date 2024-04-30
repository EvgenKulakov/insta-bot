from typing import List
from instaloader import Instaloader
from threading import Lock


class InstaloaderIterator:
    INSTALOADERS: List[Instaloader]
    INDEX: int
    LOCK: Lock

    def __init__(self, INSTALOADERS: List[Instaloader]):
        self.INSTALOADERS = INSTALOADERS
        self.INDEX = 0
        self.LOCK = Lock()

    def __next__(self):
        if len(self.INSTALOADERS) > 0:
            with self.LOCK:
                result = self.INSTALOADERS[self.INDEX]
                self.INDEX = (self.INDEX + 1) % len(self.INSTALOADERS)
                return result
        else:
            return None

    def add(self, instaloader):
        with self.LOCK:
            self.INSTALOADERS.append(instaloader)

    def remove(self, instaloader):
        with self.LOCK:
            self.INSTALOADERS.remove(instaloader)
            if self.INDEX >= len(self.INSTALOADERS):
                self.INDEX = 0

    def get_size(self):
        return len(self.INSTALOADERS)