"""
Databse for users 
"""

import logging
import sqlite3
from datetime import datetime, timedelta

from cryptography.fernet import Fernet


class Database:
    def __init__(self, db_path="database.sqlite3", encrypt_key=None):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.encrypt_key = encrypt_key or Fernet.generate_key()
        self.cipher = Fernet(self.encrypt_key)

    def migrate(self):
        # Create `users` table
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            edu_login TEXT NOT NULL,
            edu_password TEXT NOT NULL
        )
        """
        )

        # Create `jwt_tokens` table
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS jwt_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        self.connection.commit()

    def add_user(self, telegram_id, username, edu_login, edu_password):
        encrypt_password = self.cipher.encrypt(edu_password.encode())

        try:
            self.cursor.execute(
                """
                        INSERT INTO users (telegram_id, username, edu_login, edu_password)
                        VALUES (?, ?, ?, ?)
            """,
                (telegram_id, username, edu_login, encrypt_password),
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            logging.error("User with this telegram_id already exists.")

    def get_user(self, telegram_id):
        self.cursor.execute(
            """
            SELECT id, telegram_id, username, edu_login, edu_password FROM users WHERE telegram_id = ?
        """,
            (telegram_id,),
        )

        user = self.cursor.fetchone()

        if user:
            user = {
                "id": user[0],
                "telegram_id": user[1],
                "username": user[2],
                "edu_login": user[3],
                "edu_password": self.cipher.decrypt(user[4]).decode(),
            }

        return user

    def create_jwt(self, user_id, token, expires_in=3600):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.cursor.execute(
            """
        INSERT INTO jwt_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
        """,
            (user_id, token, expires_at),
        )
        self.connection.commit()

    def get_valid_jwt(self, user_id):
        self.cursor.execute(
            """
        SELECT token, expires_at FROM jwt_tokens
        WHERE user_id = ? AND expires_at > ?
        """,
            (user_id, datetime.utcnow()),
        )
        jwt = self.cursor.fetchone()
        if jwt:
            return {"token": jwt[0], "expires_at": jwt[1]}
        return None
