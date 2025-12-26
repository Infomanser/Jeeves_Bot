# handlers/notes.py
import sqlite3
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from services.db_manager import get_connection

router = Router()

@router.message(F.text.startswith("Нотатка:"))
async def add_note(message: Message):
    text = message.text.replace("Нотатка:", "").strip()
    user_id = message.from_user.id
    tags = [word for word in text.split() if word.startswith("#")]
    tags_str = ",".join(tags)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (user_id, content, tags) VALUES (?, ?, ?)', 
                   (user_id, text, tags_str))
    conn.commit()
    conn.close()
    await message.reply(f"✅ Зберіг! {tags_str}")

# Вивід списку ТЕГІВ
@router.message(F.text == "/notes")
async def show_tags(message: Message):
    user_id = message.from_user.id
    conn = get_connection()
    cursor = conn.cursor()
    
    # Беремо всі теги користувача
    cursor.execute('SELECT tags FROM notes WHERE user_id = ? AND tags != ""', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("У тебе поки немає нотаток з тегами.")
        return

    # Чистимо теги: збираємо у множину (set), щоб не було дублів, і прибираємо #
    all_tags = set()
    for row in rows:
        for tag in row['tags'].split(','):
            if tag:
                all_tags.add(tag.replace("#", ""))

    # Створюємо кнопки
    buttons = []
    for tag in sorted(all_tags):
        buttons.append([InlineKeyboardButton(text=f"📂 {tag}", callback_data=f"note_tag:{tag}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Обери категорію нотаток:", reply_markup=keyboard)

# Вивід нотаток за обраним тегом
@router.callback_query(F.data.startswith("note_tag:"))
async def show_notes_by_tag(callback: CallbackQuery):
    tag_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    conn = get_connection()
    cursor = conn.cursor()
    # Шукаємо нотатки, де в полі tags є наш тег (з решіткою)
    cursor.execute('SELECT content FROM notes WHERE user_id = ? AND tags LIKE ?', 
                   (user_id, f'%#{tag_name}%'))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.answer("Нотаток не знайдено.")
        return

    res_text = f"<b>Нотатки за тегом #{tag_name}:</b>\n\n"
    for i, row in enumerate(rows, 1):
        # Прибираємо самі теги з тексту для чистоти виводу
        clean_content = row['content']
        for word in clean_content.split():
            if word.startswith("#"):
                clean_content = clean_content.replace(word, "").strip()
        
        res_text += f"{i}. {clean_content}\n"

    await callback.message.edit_text(res_text, parse_mode="HTML")
    await callback.answer()