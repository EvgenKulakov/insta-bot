import sqlite3
from configparser import ConfigParser
from typing import List


class Service:
    PROPERTIES: ConfigParser
    DATABASE_PATH: str
    def __init__(self, properties: ConfigParser):
        self.PROPERTIES = properties
        self.DATABASE_PATH = self.PROPERTIES['DATABASE']['PATH']

    def add_profile(self, telegram_id: int, username: str):
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