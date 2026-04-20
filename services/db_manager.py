import glob
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# --- ШЛЯХИ ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_NAME = "jeeves.db"
DB_PATH = DATA_DIR / DB_NAME
BACKUP_DIR = BASE_DIR / "backups"
MAX_BACKUPS = 7

def get_connection():
    """Створює підключення до БД з підтримкою словникового виводу"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ініціалізація таблиць (викликається при старті бота)"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Таблиця користувачів (без дублювання координат)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'uk',
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

    # 4. Weather settings 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_weather (
            user_id INTEGER PRIMARY KEY,
            city_name TEXT,
            lat REAL,
            lon REAL
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("✅ База даних перевірена/ініціалізована.")

def backup_database():
    """Робить копію бази, видаляє найстаріші"""
    try:
        if not DB_PATH.exists():
            logging.warning("⚠️ База даних ще не створена, бекап скасовано.")
            return False, "Database not found"

        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = BACKUP_DIR / f"jeeves_backup_{timestamp}.db"

        shutil.copy2(DB_PATH, backup_name)
        logging.info(f"✅ Database backup created: {backup_name}")

        list_of_backups = glob.glob(str(BACKUP_DIR / "*.db"))
        list_of_backups.sort(key=os.path.getmtime)

        while len(list_of_backups) > MAX_BACKUPS:
            oldest_file = list_of_backups.pop(0)
            os.remove(oldest_file)
            logging.info(f"🗑 Rotated old backup: {oldest_file}")
            
        return True, str(backup_name)

    except Exception as e:
        logging.error(f"❌ Backup failed: {e}")
        return False, str(e)
