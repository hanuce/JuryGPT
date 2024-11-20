import sqlite3
import os


db_path = os.path.abspath('data/database.db')
print(f"Veritabanı yolu: {db_path}")
print(f"Dosya mevcut mu?: {os.path.exists(db_path)}")

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tablolar:")
for table in tables:
    print(table[0])

conn.close()