import sqlite3
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from services.db_manager import get_connection
from config import OWNER_ID

router = Router()

# --- КІМНАТА 1: ДОДАВАННЯ НОТАТОК ---
@router.message(F.text.startswith("Нотатка:"))
async def add_note(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # 1. ПЕРЕВІРКА ПРАВ
    is_allowed = False
    if user_id == OWNER_ID:
        is_allowed = True
    else:
        member = await message.chat.get_member(user_id)
        if member.status == "creator":
            is_allowed = True
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            conn.close()
            is_allowed = user_data and user_data['is_admin'] == 1

    if not is_allowed:
        await message.reply("🚫 Тільки Хазяїн, Власник групи або довірені особи можуть поповнювати базу знань.")
        return

    # 2. ПРОЦЕС ЗАПИСУ
    text = message.text.replace("Нотатка:", "").strip()
    tags = [word for word in text.split() if word.startswith("#")]
    tags_str = ",".join(tags)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (user_id, content, tags) VALUES (?, ?, ?)', 
                   (chat_id, text, tags_str))
    conn.commit()
    conn.close()

    await message.reply(f"✅ Додано в базу знань чату! {tags_str}")


# --- КІМНАТА 2: АВТОМАТИЗАЦІЯ АДМІНІВ ---
@router.message(F.text == "/trust_admins")
async def trust_all_admins(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    if message.chat.type == "private":
        await message.answer("Це працює тільки в групах.")
        return

    admins = await message.chat.get_administrators()
    conn = get_connection()
    cursor = conn.cursor()
    
    count = 0
    for admin in admins:
        if not admin.user.is_bot:
            cursor.execute('INSERT OR IGNORE INTO users (user_id, is_admin) VALUES (?, 1)', (admin.user.id,))
            count += 1
            
    conn.commit()
    conn.close()
    await message.reply(f"⚡️ {count} адмінів додано до списку довірених.")


# --- КІМНАТА 3: СПИСОК ТЕГІВ ---
@router.message(F.text == "/notes")
async def show_tags(message: Message):
    chat_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT tags FROM notes WHERE user_id = ? AND tags != ""', (chat_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("В цьому чаті поки немає бази знань.")
        return

    all_tags = set()
    for row in rows:
        for tag in row['tags'].split(','):
            if tag: all_tags.add(tag.replace("#", ""))

    buttons = [[InlineKeyboardButton(text=f"📂 {tag}", callback_data=f"note_tag:{tag}")] for tag in sorted(all_tags)]
    await message.answer("📚 База знань чату. Обери тег:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# --- КІМНАТА 4: ВИВІД НОТАТОК ---
@router.callback_query(F.data.startswith("note_tag:"))
async def show_notes_by_tag(callback: CallbackQuery):
    tag_name = callback.data.split(":")[1]
    chat_id = callback.message.chat.id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM notes WHERE user_id = ? AND tags LIKE ?', (chat_id, f'%#{tag_name}%'))
    rows = cursor.fetchall()
    conn.close()

    res_text = f"<b>📖 Знання за тегом #{tag_name}:</b>\n\n"
    for i, row in enumerate(rows, 1):
        clean_content = " ".join([word for word in row['content'].split() if not word.startswith("#")])
        res_text += f"{i}. {clean_content}\n"

    await callback.message.edit_text(res_text, parse_mode="HTML")
    await callback.answer()