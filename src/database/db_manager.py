import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self, db_path=None):
        # allow DATABASE_URL like sqlite:///pos_system.db
        if db_path is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///pos_system.db")
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "", 1)
            else:
                db_path = "pos_system.db"
        self.db_path = db_path
        self.connection = None

    def create_connection(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        print("Connection to SQLite DB successful")

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection to SQLite DB closed")
