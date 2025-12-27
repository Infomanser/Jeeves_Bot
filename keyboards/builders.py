# keyboards/builders.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import OWNER_ID, ADMIN_IDS

def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # --- ВЛАСНИК (Головна сторінка) ---
    if user_id == OWNER_ID:
        # 1 ряд: Папки
        builder.row(
            KeyboardButton(text="🔄 Керування"),
            KeyboardButton(text="🛠 Інструменти")
        )
        # 2 ряд: Папки + База
        builder.row(
            KeyboardButton(text="📂 Інфо"),
            KeyboardButton(text="📚 База знань")
        )
        # 3 ряд: Пряма дія
        builder.row(
            KeyboardButton(text="➕ Додати подію"),
            KeyboardButton(text="✍️ Додати нотатку")
        )

    # --- АДМІН (Головна сторінка) ---
    elif user_id in ADMIN_IDS:
        builder.row(
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="🌦 Погода"),
            KeyboardButton(text="📰 Новини")
        )
        builder.row(
            KeyboardButton(text="📢 Знайти телефон"),
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Кіт")
        )
        builder.row(
            KeyboardButton(text="➕ Додати подію"),
            KeyboardButton(text="✍️ Додати нотатку"),
            KeyboardButton(text="📚 База знань")
        )
    
    # Інші юзери
    else:
        return None

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

# --- ПІДМЕНЮ ДЛЯ ВЛАСНИКА ---

def get_restarts_menu() -> ReplyKeyboardMarkup:
    """Меню рестартів"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔄 Кіт"),
        KeyboardButton(text="🔄 SSH"),
        KeyboardButton(text="🔄 Тунель")
    )
    builder.row(
        KeyboardButton(text="🔄 AllSaver"),
        KeyboardButton(text="🔄 Дживс")
    )
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)

def get_tools_menu() -> ReplyKeyboardMarkup:
    """Меню інструментів та логів"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📲 Статус"),
        KeyboardButton(text="💾 Пам'ять"),
        KeyboardButton(text="💾 Бекап БД")
    )
    builder.row(
        KeyboardButton(text="🔦 Увімк"),
        KeyboardButton(text="🌑 Вимк"),
        KeyboardButton(text="📢 Знайти телефон")
    )
    builder.row(
        KeyboardButton(text="📄 Логи"),
        KeyboardButton(text="❌ Еrror log")
    )
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)

def get_info_menu() -> ReplyKeyboardMarkup:
    """Меню інформації"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🌦 Погода"),
        KeyboardButton(text="📅 Календар"),
        KeyboardButton(text="📰 Новини")
    )
    builder.row(KeyboardButton(text="⬅️ Назад"))
    return builder.as_markup(resize_keyboard=True)