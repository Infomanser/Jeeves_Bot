# keyboards/builders.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import OWNER_ID, ADMIN_IDS

def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # --- 1. ВЛАСНИК ---
    if user_id == OWNER_ID:
        builder.button(text="🔄 Керування")
        builder.button(text="🛠 Інструменти")
        builder.button(text="📂 Інфо")
        builder.button(text="📚 База знань")
        builder.button(text="➕ Додати подію")
        builder.button(text="✍️ Додати нотатку")
        builder.adjust(2, 2, 2)
        return builder.as_markup(resize_keyboard=True)

    # --- 2. БАЗОВІ КНОПКИ (ДЛЯ АДМІНІВ ТА ЮЗЕРІВ) ---
    builder.button(text="📅 Календар")
    builder.button(text="📰 Новини")
    builder.button(text="🌦 Обрати місто")
    builder.button(text="🌦 Погода")
    builder.button(text="🌦 Погода на тиждень")

    # --- 3. ДОДАТКОВІ КНОПКИ ДЛЯ АДМІНІВ ---
    if user_id in ADMIN_IDS:
        builder.button(text="📢 Знайти телефон")
        builder.button(text="🔄 AllSaver")
        builder.button(text="🔄 Кіт")
        # Сітка для адміна (базові + адмінські)
        builder.adjust(2, 1, 2, 3) 
    else:
        # Сітка для звичайного юзера
        builder.button(text="➕ Додати подію")
        builder.button(text="✍️ Додати нотатку")
        builder.button(text="📚 База знань")
        builder.adjust(2, 1, 2, 2, 1)

    return builder.as_markup(resize_keyboard=True)

# --- ПІДМЕНЮ ДЛЯ ВЛАСНИКА ---
def get_restarts_menu() -> ReplyKeyboardMarkup:
    """Меню рестартів"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Кіт")
    builder.button(text="🔄 SSH")
    builder.button(text="🔄 Тунель")
    builder.button(text="🔄 AllSaver")
    builder.button(text="🔄 Дживс")
    builder.button(text="⬅️ Назад")
    builder.adjust(3, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_tools_menu() -> ReplyKeyboardMarkup:
    """Меню інструментів та логів"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📲 Статус")
    builder.button(text="💾 Пам'ять")
    builder.button(text="💾 Бекап БД")
    builder.button(text="🔦 Увімк")
    builder.button(text="🌑 Вимк")
    builder.button(text="📢 Знайти телефон")
    builder.button(text="📄 Логи")
    builder.button(text="❌ Еrror log")
    builder.button(text="⬅️ Назад")
    builder.adjust(3, 3, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_info_menu() -> ReplyKeyboardMarkup:
    """Меню інформації"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🌦 Обрати місто")
    builder.button(text="🌦 Погода")
    builder.button(text="🌦 Погода на тиждень")
    builder.button(text="📅 Календар")
    builder.button(text="📰 Новини")
    builder.button(text="⬅️ Назад")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
