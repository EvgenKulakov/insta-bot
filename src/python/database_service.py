import sqlite3
from configparser import ConfigParser
from typing import List
from threading import Lock
from dtos import SuccessFailDTO


class Service:
    PROPERTIES: ConfigParser
    DATABASE_PATH: str
    LOCK: Lock
    def __init__(self, properties: ConfigParser):
        self.PROPERTIES = properties
        self.DATABASE_PATH = self.PROPERTIES['PATHS']['PATH_OS'] + 'data/profiles.db'
        self.LOCK = Lock()

    def add_profile(self, telegram_id: int, username: str):
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO profiles_history (telegram_id, username)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM profiles_history WHERE telegram_id = ? AND username = ?
                )
                """,
                (telegram_id, username, telegram_id, username)
            )
            conn.commit()
            cursor.close()
            conn.close()

    def get_profiles(self, telegram_id: int) -> List[str]:
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM profiles_history WHERE telegram_id = ?", (telegram_id,))
            usernames: List[str] = []
            for profile in cursor.fetchall():
                usernames.append(profile[0])
            cursor.close()
            conn.close()
            return usernames

    def remove_profile(self, telegram_id: int, username: str) -> List[str]:
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                '''
                DELETE FROM profiles_history
                WHERE telegram_id = ? AND username = ?
                AND EXISTS(
                    SELECT 1 FROM profiles_history
                    WHERE telegram_id = ? AND username = ?
                )
                ''',
                (telegram_id, username, telegram_id, username)
            )
            conn.commit()
            cursor.execute("SELECT username FROM profiles_history WHERE telegram_id = ?", (telegram_id,))
            usernames: List[str] = []
            for profile in cursor.fetchall():
                usernames.append(profile[0])
            cursor.close()
            conn.close()
            return usernames

    def add_success_fail(self, username: str, type: str):
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO success_fail_profiles (username, type)
                VALUES (?, ?)
                """,
                (username, type)
            )
            conn.commit()
            cursor.close()
            conn.close()

    def get_success_fail(self, username: str):
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM success_fail_profiles WHERE username = ?", (username,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                return SuccessFailDTO(row[1], row[2])
            else:
                return None