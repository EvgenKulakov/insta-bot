from typing import List
from threading import Lock
from lock_context_wrappers import InstaloaderWrapper


class InstaloaderIterator:
    INSTALOADERS: List[InstaloaderWrapper]
    INDEX: int
    LOCK: Lock

    def __init__(self, instaloaders: List[InstaloaderWrapper]):
        self.INSTALOADERS = instaloaders
        self.INDEX = 0
        self.LOCK = Lock()

    def next(self):
        with self.LOCK:
            if len(self.INSTALOADERS) > 0:
                self.INDEX = (self.INDEX + 1) % len(self.INSTALOADERS)
                result = self.INSTALOADERS[self.INDEX]
                return result
            else:
                return None

    def get_without_iteration(self):
        with self.LOCK:
            if len(self.INSTALOADERS) > 0:
                    return self.INSTALOADERS[self.INDEX]
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
        with self.LOCK:
            return len(self.INSTALOADERS)