import os
import sqlite3
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from groq import Groq

# Перевір config.py: там мають бути OWNER_ID та GROQ_API_KEY
from config import OWNER_ID, GROQ_API_KEY
from services.db_manager import get_connection

router = Router()

# --- 0. МІГРАЦІЯ БД (Створення таблиці локальної довіри) ---
try:
    conn = get_connection()
    cursor = conn.cursor()
    # Таблиця зв'язує: КОНКРЕТНИЙ ЧАТ <-> КОНКРЕТНИЙ ЮЗЕР
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_trust (
            chat_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    conn.commit()
    conn.close()
except Exception as e:
    logging.error(f"DB Init Error: {e}")

# Ініціалізація Groq
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logging.error(f"Groq Init Error: {e}")
    client = None

class NoteState(StatesGroup):
    waiting_for_content = State()


# --- 1. СИСТЕМА ПРАВ (SECURITY CORE) ---

def check_permissions(user_id: int, chat_id: int, member_status: str) -> bool:
    """
    Перевіряє, чи може юзер писати/читати базу в ЦЬОМУ чаті.
    """
    # 1. ROOT: Бог у всіх чатах
    if user_id == OWNER_ID:
        return True
    
    # 2. CREATOR: Бог тільки в СВОЄМУ чаті
    if member_status == "creator":
        return True
    
    # 3. TRUSTED: Перевіряємо, чи є він у "білому списку" ЦЬОГО чату
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM chat_trust WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
    is_trusted = cursor.fetchone()
    conn.close()
    
    return is_trusted is not None

def can_manage_trust(user_id: int, member_status: str) -> bool:
    """
    Хто може натискати /trust та /untrust?
    Тільки ROOT (глобально) або CREATOR (локально).
    Звичайні адміни, навіть "трастед", не можуть додавати інших.
    """
    return user_id == OWNER_ID or member_status == "creator"

def save_note_to_db(chat_id: int, text: str):
    """Зберігає нотатку прив'язану до chat_id"""
    tags = [word for word in text.split() if word.startswith("#")]
    tags_str = ",".join(tags)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (user_id, content, tags) VALUES (?, ?, ?)', 
                   (chat_id, text, tags_str))
    conn.commit()
    conn.close()
    return tags_str


# --- 2. ОБРОБКА ГОЛОСУ (GROQ + WHISPER) ---
@router.message(F.voice)
async def handle_voice_note(message: Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    # Отримуємо статус юзера саме тут
    member = await message.chat.get_member(user_id)

    # Перевірка прав
    if not check_permissions(user_id, chat_id, member.status):
        return # Мовчки ігноруємо чужих

    if not client:
        await message.reply("⚠️ Groq API не налаштовано.")
        return

    status_msg = await message.reply("👂 Слухаю...")
    filename = f"voice_{user_id}_{message.message_id}.ogg"

    try:
        await bot.download(message.voice, destination=filename)
        
        # Відправляємо OGG напряму в Groq
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                response_format="json"
            )
        
        raw_text = transcription.text
        final_text = raw_text
        header = "🎙 <b>Голосова нотатка:</b>"

        if len(raw_text.split()) > 30:
            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Ти секретар. Оформи цей текст як чітку нотатку українською. Виділи суть. Коли робиш summary, придумай і додай 1-2 теги самостійно, якщо юзер не сказав"},
                        {"role": "user", "content": raw_text}
                    ]
                )
                final_text = f"{chat_completion.choices[0].message.content}\n\n<i>(Оригінал: {raw_text[:60]}...)</i>"
                header = "🧠 <b>Оброблено:</b>"
            except Exception: pass

        tags_found = save_note_to_db(chat_id, final_text)
        await status_msg.edit_text(f"{header}\n{final_text}\n\n🏷 {tags_found or 'без тегів'}", parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Помилка: {e}")
    finally:
        if os.path.exists(filename): os.remove(filename)


# --- 3. FSM (ІНТЕРАКТИВНИЙ ЗАПИС) ---
@router.message(F.text.lower().in_({"запиши", "нотатка", "додати нотатку"}))
async def start_interactive_note(message: Message, state: FSMContext):
    member = await message.chat.get_member(message.from_user.id)
    if not check_permissions(message.from_user.id, message.chat.id, member.status):
        await message.reply("🚫 У тебе немає прав писати в базу цього чату.")
        return

    await message.reply("✍️ Що записати? (Надішли текст)")
    await state.set_state(NoteState.waiting_for_content)

@router.message(NoteState.waiting_for_content)
async def save_interactive_note(message: Message, state: FSMContext):
    save_note_to_db(message.chat.id, message.text)
    await message.reply("✅ Збережено!")
    await state.clear()


# --- 4. ШВИДКИЙ ЗАПИС (Legacy) ---
@router.message(F.text.startswith("Нотатка:"))
async def add_note_fast(message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if not check_permissions(message.from_user.id, message.chat.id, member.status):
        return
    
    text = message.text.replace("Нотатка:", "").strip()
    if not text: return
    
    save_note_to_db(message.chat.id, text)
    await message.reply("✅")


# --- 5. КЕРУВАННЯ ЛОКАЛЬНОЮ ДОВІРОЮ ---

@router.message(F.text == "/trust")
async def trust_user(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.chat.get_member(user_id)
    
    # Тільки Root або Creator
    if not can_manage_trust(user_id, member.status):
        await message.reply("🚫 Тільки Власник чату може роздавати права.")
        return
        
    if not message.reply_to_message:
        await message.reply("☝️ Зроби Reply (відповідь) на повідомлення користувача.")
        return

    target_user = message.reply_to_message.from_user
    if target_user.is_bot: return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO chat_trust (chat_id, user_id) VALUES (?, ?)', (chat_id, target_user.id))
    conn.commit()
    conn.close()
    
    await message.reply(f"🤝 <b>{target_user.full_name}</b> тепер має доступ до бази знань <b>цього чату</b>.", parse_mode="HTML")

@router.message(F.text == "/untrust")
async def untrust_user(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.chat.get_member(user_id)
    
    if not can_manage_trust(user_id, member.status):
        return

    if not message.reply_to_message:
        await message.reply("☝️ Зроби Reply.")
        return

    target_user = message.reply_to_message.from_user
    
    if target_user.id == OWNER_ID:
        await message.reply("👑 Рута не можна чіпати.")
        return
    if member.status == "creator" and target_user.id == user_id:
        await message.reply("🤨 Ти не можеш звільнити сам себе.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_trust WHERE chat_id = ? AND user_id = ?', (chat_id, target_user.id))
    conn.commit()
    conn.close()
    
    await message.reply(f"👋 <b>{target_user.full_name}</b> видалений зі списку довірених у цьому чаті.", parse_mode="HTML")

@router.message(F.text == "/trust_admins")
async def trust_all_local_admins(message: Message):
    user_id = message.from_user.id
    member = await message.chat.get_member(user_id)

    if not can_manage_trust(user_id, member.status):
        return

    if message.chat.type == "private":
        return

    admins = await message.chat.get_administrators()
    conn = get_connection()
    cursor = conn.cursor()
    
    count = 0
    chat_id = message.chat.id
    for admin in admins:
        if not admin.user.is_bot:
            cursor.execute('INSERT OR IGNORE INTO chat_trust (chat_id, user_id) VALUES (?, ?)', (chat_id, admin.user.id,))
            count += 1
            
    conn.commit()
    conn.close()
    await message.reply(f"⚡️ {count} адмінів додано до білого списку <b>цього чату</b>.", parse_mode="HTML")


# --- 6. ПЕРЕГЛЯД ТА ПОШУК ---

@router.message(F.text == "/notes")
@router.message(F.text == "📚 База знань")
async def show_tags(message: Message):
    chat_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT tags FROM notes WHERE user_id = ?', (chat_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📭 База порожня.")
        return

    all_tags = set()
    has_untagged = False 

    for row in rows:
        tags_raw = row['tags']
        if tags_raw:
            for tag in tags_raw.split(','):
                if tag: all_tags.add(tag.replace("#", ""))
        else:
            has_untagged = True

    buttons = []
    sorted_tags = sorted(list(all_tags))
    
    # Кнопки тегів по 2 в ряд
    temp_row = []
    for tag in sorted_tags:
        temp_row.append(InlineKeyboardButton(text=f"📂 {tag}", callback_data=f"list_notes:{tag}"))
        if len(temp_row) == 2:
            buttons.append(temp_row)
            temp_row = []
    if temp_row:
        buttons.append(temp_row)

    if has_untagged:
        buttons.append([InlineKeyboardButton(text="📥 Інше (без тегів)", callback_data="list_notes:__empty__")])
    
    # Кнопка закриття меню
    buttons.append([InlineKeyboardButton(text="❌ Закрити меню", callback_data="delete_msg")])

    await message.answer("📚 <b>База знань чату.</b> Обери категорію:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


# 1. СПИСОК НОТАТОК У КАТЕГОРІЇ
@router.callback_query(F.data.startswith("list_notes:"))
async def show_notes_list(callback: CallbackQuery):
    tag_name = callback.data.split(":")[1]
    chat_id = callback.message.chat.id
    
    conn = get_connection()
    cursor = conn.cursor()

    if tag_name == "__empty__":
        # Тягнемо ID і початок тексту
        cursor.execute('SELECT id, content FROM notes WHERE user_id = ? AND tags = ""', (chat_id,))
        header = "📥 <b>Без тегів:</b>"
    else:
        cursor.execute('SELECT id, content FROM notes WHERE user_id = ? AND tags LIKE ?', (chat_id, f'%#{tag_name}%'))
        header = f"<b>📂 Категорія #{tag_name}:</b>"

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.answer("Пусто...", show_alert=True)
        return

    buttons = []
    for row in rows:
        note_id = row['id']
        # Обрізаємо текст для краси кнопки (перші 30 символів)
        preview_text = row['content'][:30].replace("\n", " ") + "..."
        buttons.append([InlineKeyboardButton(text=f"🔹 {preview_text}", callback_data=f"view_note:{note_id}:{tag_name}")])

    # Кнопка "Назад до тегів"
    buttons.append([InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="back_to_tags")])

    await callback.message.edit_text(
        f"{header}\n⬇️ <i>Обери нотатку, щоб прочитати або видалити:</i>", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# 2. ПЕРЕГЛЯД КОНКРЕТНОЇ НОТАТКИ (ДЕТАЛІ)
@router.callback_query(F.data.startswith("view_note:"))
async def view_single_note(callback: CallbackQuery):
    _, note_id, tag_context = callback.data.split(":")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content, tags FROM notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await callback.answer("Ця нотатка вже видалена.", show_alert=True)
        # Оновлюємо список, бо нотатки нема
        await show_notes_list(callback) 
        return

    full_text = row['content']
    tags = row['tags'] or "без тегів"

    # Кнопки дій
    buttons = [
        [InlineKeyboardButton(text="🗑 Видалити", callback_data=f"del_note:{note_id}:{tag_context}")],
        [InlineKeyboardButton(text="🔙 Назад до списку", callback_data=f"list_notes:{tag_context}")]
    ]

    await callback.message.edit_text(
        f"📝 <b>Нотатка:</b>\n\n{full_text}\n\n🏷 <i>{tags}</i>", 
        parse_mode="HTML", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


# 3. ВИДАЛЕННЯ НОТАТКИ
@router.callback_query(F.data.startswith("del_note:"))
async def delete_single_note(callback: CallbackQuery):
    _, note_id, tag_context = callback.data.split(":")
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    member = await callback.message.chat.get_member(user_id)

    # ПЕРЕВІРКА ПРАВ
    if not check_permissions(user_id, chat_id, member.status):
        await callback.answer("⛔️ Видаляти можуть тільки Адміни або Довірені!", show_alert=True)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

    await callback.answer("✅ Нотатку видалено!", show_alert=True)
    

    callback.data = f"list_notes:{tag_context}"
    await show_notes_list(callback)


# 4. НАВІГАЦІЯ: НАЗАД ДО ТЕГІВ
@router.callback_query(F.data == "back_to_tags")
async def back_to_tags_handler(callback: CallbackQuery):
    await show_tags(callback.message)
    await callback.message.delete()


@router.callback_query(F.data == "delete_msg")
async def delete_msg_handler(callback: CallbackQuery):
    await callback.message.delete()