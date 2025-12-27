# services/db_manager.py
import sqlite3
import os
import shutil
import glob
from datetime import datetime
import logging

# Шлях до папки з даними
DATA_DIR = "data"
DB_NAME = "jeeves_database.db"
DB_PATH = os.path.join(DATA_DIR, DB_NAME)
BACKUP_DIR = "backups"
MAX_BACKUPS = 7

def get_connection():
    """Створює підключення до БД з підтримкою словникового виводу"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ініціалізація таблиць (викликається при старті бота)"""
    
    # Переконуємось, що папка data існує
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Таблиця користувачів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'uk',
            city_name TEXT,
            lat REAL,
            lon REAL,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # 2. Таблиця календаря
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_date TEXT,
            event_text TEXT,
            link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Таблиця нотатника
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            tags TEXT,
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("✅ База даних перевірена/ініціалізована.")

def backup_database():
    """Робить копію бази, видаляє найстаріші"""
    try:
        # Перевіряємо, чи існує сама база
        if not os.path.exists(DB_PATH):
            logging.warning("⚠️ База даних ще не створена, бекап скасовано.")
            return False, "Database not found"

        # Створюємо папку бекапів
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = os.path.join(BACKUP_DIR, f"jeeves_backup_{timestamp}.db")

        # Копіюємо з папки data в backups
        shutil.copy2(DB_PATH, backup_name)
        logging.info(f"✅ Database backup created: {backup_name}")

        # Ротація
        list_of_backups = glob.glob(os.path.join(BACKUP_DIR, "*.db"))
        list_of_backups.sort(key=os.path.getmtime)

        while len(list_of_backups) > MAX_BACKUPS:
            oldest_file = list_of_backups.pop(0)
            os.remove(oldest_file)
            logging.info(f"🗑 Rotated old backup: {oldest_file}")
            
        return True, backup_name

    except Exception as e:
        logging.error(f"❌ Backup failed: {e}")
        return False, str(e)