# handlers/notes.py
import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from config import OWNER_ID, ADMIN_IDS
from services.db_manager import get_connection
from services import termux_api

# Спробуємо підключити Groq, якщо немає - фолбек
try:
    from groq import Groq
    from config import GROQ_API_KEY
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except ImportError:
    groq_client = None

router = Router()

# --- FSM STATES ---
class NoteStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_tags = State()

# --- ПРАВА ДОСТУПУ ---
def check_permissions(user_id, chat_id, member_status):
    if user_id == OWNER_ID: return True
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT trust_level FROM chat_trust WHERE chat_id = ?', (chat_id,))
    row = cursor.fetchone()
    conn.close()

    trust_level = row['trust_level'] if row else 'guest'

    if trust_level == 'guest': return False
    if trust_level == 'admins_only':
        return member_status in ['administrator', 'creator'] or user_id in ADMIN_IDS
    if trust_level == 'all': return True
    return False

# --- 1. ДОДАВАННЯ НОТАТКИ (ТЕКСТ, ГОЛОС, ФОТО) ---

@router.message(Command("note"))
async def start_note(message: Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await message.chat.get_member(user_id)

    if not check_permissions(user_id, chat_id, member.status):
        await message.answer("⛔️ У цьому чаті я нотатки не приймаю.")
        return

    # Якщо команда введена з текстом: /note купити хліба #дім
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        content = args[1]
        tags = extract_tags(content)
        save_note_to_db(chat_id, content, tags)
        await message.answer(f"✅ Записав: <b>{content[:50]}...</b>", parse_mode="HTML")
        return

    await message.answer("✍️ Що записати? (Надішли текст, голосове або <b>фото</b>)")
    await state.set_state(NoteStates.waiting_for_content)

@router.message(NoteStates.waiting_for_content)
async def process_content(message: Message, state: FSMContext):
    content_text = ""
    file_id = None
    media_type = None

    # 1. ОБРОБКА ФОТО
    if message.photo:
        # Беремо найбільше фото (останнє в списку)
        file_id = message.photo[-1].file_id
        media_type = "photo"
        # Текст беремо з підпису (caption), якщо є
        content_text = message.caption or "Фото без опису"

    # 2. ОБРОБКА ГОЛОСУ
    elif message.voice:
        if not groq_client:
            await message.answer("⚠️ Groq не налаштований, не можу розпізнати голос.")
            return
        
        processing_msg = await message.answer("👂 Слухаю і записую...")
        try:
            file_info = await message.bot.get_file(message.voice.file_id)
            file_path = file_info.file_path
            
            # Завантажуємо файл
            voice_file = await message.bot.download_file(file_path)
            
            # Whisper транскрипція
            transcription = groq_client.audio.transcriptions.create(
                file=("voice.ogg", voice_file.read()),
                model="whisper-large-v3",
                language="uk"
            )
            content_text = transcription.text
            await processing_msg.delete()
        except Exception as e:
            await processing_msg.edit_text(f"❌ Помилка розпізнавання: {e}")
            return
    
    # 3. ОБРОБКА ТЕКСТУ
    elif message.text:
        content_text = message.text
    
    else:
        await message.answer("🤔 Я розумію тільки текст, голос або фото.")
        return

    # Зберігаємо тимчасово
    await state.update_data(content=content_text, file_id=file_id, media_type=media_type)
    
    # Спробуємо AI для тегів (якщо є текст)
    suggested_tags = ""
    if groq_client and len(content_text) > 10:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f"Прочитай текст і виділи 1-3 ключові категорії (теги) українською. Поверни ТІЛЬКИ теги через кому, без пояснень. Текст: {content_text}"
                }],
                model="llama3-8b-8192",
            )
            suggested_tags = chat_completion.choices[0].message.content
        except: pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Зберегти так", callback_data="save_note")],
        [InlineKeyboardButton(text="✍️ Додати свої теги", callback_data="add_tags")]
    ])

    preview = content_text if len(content_text) < 100 else content_text[:100] + "..."
    msg_text = f"📝 <b>Перевір:</b>\n{preview}\n\n🏷 <i>AI Теги: {suggested_tags}</i>"
    
    # Якщо це фото, відповідаємо з прив'язкою до нього
    if media_type == "photo":
        await message.answer_photo(photo=file_id, caption=msg_text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
        
    await state.update_data(ai_tags=suggested_tags)


@router.callback_query(F.data == "save_note")
async def save_note_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    content = data.get("content")
    ai_tags = data.get("ai_tags", "")
    file_id = data.get("file_id")
    media_type = data.get("media_type")

    # Форматуємо теги
    clean_tags = []
    if ai_tags:
        for t in ai_tags.split(','):
            tag = t.strip().replace(" ", "_").replace("#", "")
            if tag: clean_tags.append(f"#{tag}")
    
    final_tags = " ".join(clean_tags)
    
    save_note_to_db(callback.message.chat.id, content, final_tags, file_id, media_type)
    
    await callback.message.delete()
    await callback.message.answer(f"✅ Збережено в категорію: {final_tags or 'Без тегів'}")
    await state.clear()


@router.callback_query(F.data == "add_tags")
async def ask_tags(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏷 Введи теги через кому (наприклад: робота, ідеї):")
    await state.set_state(NoteStates.waiting_for_tags)
    await callback.answer()


@router.message(NoteStates.waiting_for_tags)
async def process_manual_tags(message: Message, state: FSMContext):
    data = await state.get_data()
    content = data.get("content")
    file_id = data.get("file_id")
    media_type = data.get("media_type")
    
    user_tags = message.text
    clean_tags = []
    for t in user_tags.split(','):
        tag = t.strip().replace(" ", "_").replace("#", "")
        if tag: clean_tags.append(f"#{tag}")
    
    final_tags = " ".join(clean_tags)
    
    save_note_to_db(message.chat.id, content, final_tags, file_id, media_type)
    await message.answer(f"✅ Збережено з тегами: {final_tags}")
    await state.clear()


# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def extract_tags(text):
    return " ".join([word for word in text.split() if word.startswith("#")])

def save_note_to_db(user_id, content, tags, file_id=None, media_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO notes (user_id, content, tags, file_id, media_type) VALUES (?, ?, ?, ?, ?)', 
        (user_id, content, tags, file_id, media_type)
    )
    conn.commit()
    conn.close()


# --- 6. ПЕРЕГЛЯД ТА ПОШУК ---

@router.message(F.text == "/notes")
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
            # Обробка різних розділювачів (пробіл або кома)
            if " " in tags_raw and "," not in tags_raw:
                 for t in tags_raw.split(): 
                     if t: all_tags.add(t.replace("#", ""))
            else:
                 for t in tags_raw.split(','):
                    tag = t.strip()
                    if tag: all_tags.add(tag.replace("#", ""))
        else:
            has_untagged = True

    buttons = []
    sorted_tags = sorted(list(all_tags))
    
    temp_row = []
    for tag in sorted_tags:
        if not tag: continue
        temp_row.append(InlineKeyboardButton(text=f"📂 {tag}", callback_data=f"list_notes:{tag}"))
        if len(temp_row) == 2:
            buttons.append(temp_row)
            temp_row = []
    if temp_row:
        buttons.append(temp_row)

    if has_untagged:
        buttons.append([InlineKeyboardButton(text="📥 Інше (без тегів)", callback_data="list_notes:__empty__")])
    
    buttons.append([InlineKeyboardButton(text="❌ Закрити меню", callback_data="delete_msg")])

    await message.answer("📚 <b>База знань чату.</b> Обери категорію:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


@router.callback_query(F.data.startswith("list_notes:"))
async def show_notes_list(callback: CallbackQuery):
    tag_name = callback.data.split(":")[1]
    chat_id = callback.message.chat.id
    
    conn = get_connection()
    cursor = conn.cursor()

    if tag_name == "__empty__":
        cursor.execute('SELECT id, content, media_type FROM notes WHERE user_id = ? AND (tags = "" OR tags IS NULL)', (chat_id,))
        header = "📥 <b>Без тегів:</b>"
    else:
        cursor.execute('SELECT id, content, media_type FROM notes WHERE user_id = ? AND tags LIKE ?', (chat_id, f'%#{tag_name}%'))
        header = f"<b>📂 Категорія #{tag_name}:</b>"

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await callback.answer("Пусто...", show_alert=True)
        return

    buttons = []
    for row in rows:
        note_id = row['id']
        note_content = row['content']
        is_photo = row['media_type'] == 'photo'
        
        # Іконка: 🖼 якщо фото, 🔹 якщо текст
        icon = "🖼" if is_photo else "🔹"
        preview_text = note_content[:25].replace("\n", " ") + "..." if note_content else "Без опису"
        
        buttons.append([InlineKeyboardButton(text=f"{icon} {preview_text}", callback_data=f"view_note:{note_id}:{tag_name}")])

    buttons.append([InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="back_to_tags")])

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            f"{header}\n⬇️ <i>Обери нотатку:</i>", 
            parse_mode="HTML", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    else:
        await callback.message.edit_text(
            f"{header}\n⬇️ <i>Обери нотатку:</i>", 
            parse_mode="HTML", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("view_note:"))
async def view_single_note(callback: CallbackQuery):
    _, note_id, tag_context = callback.data.split(":")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content, tags, file_id, media_type FROM notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await callback.answer("Нотатка видалена.", show_alert=True)
        new_callback = callback.model_copy(update={"data": f"list_notes:{tag_context}"})
        await show_notes_list(new_callback)
        return

    full_text = row['content'] or "Без опису"
    tags = row['tags'] or ""
    file_id = row['file_id']
    media_type = row['media_type']

    buttons = [
        [InlineKeyboardButton(text="🗑 Видалити", callback_data=f"del_note:{note_id}:{tag_context}")],
        [InlineKeyboardButton(text="🔙 Назад до списку", callback_data=f"list_notes:{tag_context}")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    caption_text = f"📝 <b>Нотатка:</b>\n\n{full_text}\n\n🏷 <i>{tags}</i>"

    # Видаляємо старе повідомлення (щоб уникнути мішанини фото/текст)
    await callback.message.delete()

    if media_type == 'photo' and file_id:
        await callback.message.answer_photo(photo=file_id, caption=caption_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.answer(caption_text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data.startswith("del_note:"))
async def delete_single_note(callback: CallbackQuery):
    _, note_id, tag_context = callback.data.split(":")
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    member = await callback.message.chat.get_member(user_id)

    if not check_permissions(user_id, chat_id, member.status):
        await callback.answer("⛔️ Немає прав!", show_alert=True)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

    await callback.answer("✅ Видалено!", show_alert=True)
    
    new_callback = callback.model_copy(update={"data": f"list_notes:{tag_context}"})
    await show_notes_list(new_callback)

@router.callback_query(F.data == "back_to_tags")
async def back_to_tags_handler(callback: CallbackQuery):
    await callback.message.delete()
    await show_tags(callback.message) 

@router.callback_query(F.data == "delete_msg")
async def delete_msg_handler(callback: CallbackQuery):
    await callback.message.delete()