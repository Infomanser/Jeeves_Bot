import sqlite3
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from services.db_manager import get_connection

router = Router()

@router.message(F.text.startswith("Нотатка:"))
async def add_note(message: Message):
    text = message.text.replace("Нотатка:", "").strip()
    user_id = message.from_user.id
    
    # Витягуємо теги (слова, що починаються з #)
    tags = [word for word in text.split() if word.startswith("#")]
    tags_str = ",".join(tags)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (user_id, content, tags)
        VALUES (?, ?, ?)
    ''', (user_id, text, tags_str))
    conn.commit()
    conn.close()
    
    await message.reply(f"✅ Зберіг у нотатки! {'Теги: ' + tags_str if tags_str else ''}")
