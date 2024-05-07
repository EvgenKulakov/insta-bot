import sqlite3
from configparser import ConfigParser
from typing import List
from threading import Lock
from dtos import ProfileDTO


class Service:
    PROPERTIES: ConfigParser
    DATABASE_PATH: str
    LOCK: Lock
    def __init__(self, properties: ConfigParser):
        self.PROPERTIES = properties
        self.DATABASE_PATH = self.PROPERTIES['PATHS']['PATH_OS'] + 'data/profiles.db'
        self.LOCK = Lock()

    def add_history(self, telegram_id: int, username: str):
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

    def get_history(self, telegram_id: int) -> List[str]:
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

    def remove_history(self, telegram_id: int, username: str) -> List[str]:
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


    def add_profile_in_cache(self, username: str, full_name: str, userid: int):
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO profiles_cache (username, full_name, userid, success)
                VALUES (?, ?, ?, ?)
                """,
                (username, full_name, userid, 'success')
            )
            conn.commit()
            cursor.close()
            conn.close()


    def add_fail_in_cache(self, username: str):
        conn = sqlite3.connect(self.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO profiles_cache (username, success)
            VALUES (?, ?)
            """,
            (username, 'fail')
        )
        conn.commit()
        cursor.close()
        conn.close()

    def get_profile_cache(self, username: str) -> ProfileDTO | None:
        with self.LOCK:
            conn = sqlite3.connect(self.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles_cache WHERE username = ?", (username,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                if row[4] == 'success':
                    profile = ProfileDTO(username=row[1], full_name=row[2], userid=row[3], success=row[4])
                    return profile
                if row[4] == 'fail':
                    profile = ProfileDTO(username=row[1], success=row[4])
                    return profile
            else: return None