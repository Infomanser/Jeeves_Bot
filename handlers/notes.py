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


# --- 6. ПЕРЕГЛЯД ТА ПОШУК (Тільки для своїх) ---
# handlers/notes.py (частина файлу)

# --- 6. ПЕРЕГЛЯД ТА ПОШУК ---
@router.message(F.text == "/notes")
async def show_tags(message: Message):
    chat_id = message.chat.id
    conn = get_connection()
    cursor = conn.cursor()
    # 1. Прибираємо умову 'AND tags != ""', беремо ВСЕ
    cursor.execute('SELECT tags FROM notes WHERE user_id = ?', (chat_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📭 База порожня.")
        return

    all_tags = set()
    has_untagged = False # Прапорець: чи є нотатки-сироти?

    for row in rows:
        tags_raw = row['tags']
        if tags_raw:
            # Якщо теги є, додаємо їх в набір
            for tag in tags_raw.split(','):
                if tag: all_tags.add(tag.replace("#", ""))
        else:
            # Якщо тегів немає, піднімаємо прапорець
            has_untagged = True

    buttons = []
    sorted_tags = sorted(list(all_tags))
    
    # Формуємо кнопки тегів (по 2 в ряд)
    temp_row = []
    for tag in sorted_tags:
        temp_row.append(InlineKeyboardButton(text=f"📂 {tag}", callback_data=f"note_tag:{tag}"))
        if len(temp_row) == 2:
            buttons.append(temp_row)
            temp_row = []
    if temp_row:
        buttons.append(temp_row)

    # 2. Якщо є нотатки без тегів - додаємо окрему кнопку в кінці
    if has_untagged:
        buttons.append([InlineKeyboardButton(text="📥 Інше (без тегів)", callback_data="note_tag:__empty__")])

    await message.answer("📚 <b>База знань чату.</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


@router.callback_query(F.data.startswith("note_tag:"))
async def show_notes_by_tag(callback: CallbackQuery):
    tag_name = callback.data.split(":")[1]
    chat_id = callback.message.chat.id
    
    conn = get_connection()
    cursor = conn.cursor()

    # 3. Обробка звичайних тегів vs "Без тегів"
    if tag_name == "__empty__":
        # Шукаємо нотатки, де поле tags пусте
        cursor.execute('SELECT content FROM notes WHERE user_id = ? AND tags = ""', (chat_id,))
        header = "📥 <b>Нотатки без тегів:</b>"
    else:
        # Шукаємо за конкретним хештегом
        cursor.execute('SELECT content FROM notes WHERE user_id = ? AND tags LIKE ?', (chat_id, f'%#{tag_name}%'))
        header = f"<b>📖 #{tag_name}:</b>"

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.answer("Пусто...", show_alert=True)
        return

    res_text = f"{header}\n\n"
    for i, row in enumerate(rows, 1):
        content = row['content']
        res_text += f"🔹 {content}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Закрити", callback_data="delete_msg")]])
    
    try: await callback.message.edit_text(res_text, parse_mode="HTML", reply_markup=kb)
    except: await callback.message.answer(res_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "delete_msg")
async def delete_msg_handler(callback: CallbackQuery):
    await callback.message.delete()