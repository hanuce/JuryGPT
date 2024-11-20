# backend/database.py

import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        # Debate tablosunu oluşturuyoruz
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS debates (
                                debate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                debate_name TEXT,
                                school_name TEXT)''')

        # Users tablosunu oluşturuyoruz, her kullanıcı bir debate_id'ye sahip olacak
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT,
                                class_id INTEGER,
                                debate_id INTEGER,
                                FOREIGN KEY(debate_id) REFERENCES debates(debate_id))''')
        self.connection.commit()

    def insert_debate(self, debate_name, school_name):
        # Yeni bir münazara kaydediyoruz
        self.cursor.execute("INSERT INTO debates (debate_name, school_name) VALUES (?, ?)", (debate_name, school_name))
        self.connection.commit()

    def insert_user(self, name, class_id, debate_id):
        # Kullanıcıyı veritabanına ekliyoruz
        self.cursor.execute("INSERT INTO users (name, class_id, debate_id) VALUES (?, ?, ?)", (name, class_id, debate_id))
        self.connection.commit()

    def get_all_debates(self):
        # Tüm münazara bilgilerini alıyoruz
        self.cursor.execute("SELECT * FROM debates")
        return self.cursor.fetchall()

    def get_all_users(self):
        # Tüm kullanıcıları alıyoruz
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
