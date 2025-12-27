import sqlite3
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import OWNER_ID, ADMIN_IDS


def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    print(f"DEBUG: Мій ID={user_id}, OWNER_ID={OWNER_ID}, Рівні? {user_id == OWNER_ID}") # <-- ДОДАЙ ЦЕ
    builder = ReplyKeyboardBuilder()
    """
    Генерує меню на основі ID користувача.
    Власник отримує повний пульт керування (6 рядів).
    Адміни отримують базовий набір (3 ряди).
    Ліві юзери не отримують нічого.
    """
    builder = ReplyKeyboardBuilder()

    # --- ВЛАСНИК ---
    if user_id == OWNER_ID:
        # 1 ряд: Статус, Ліхтар
        builder.row(
            KeyboardButton(text="📲 Статус"),
            KeyboardButton(text="🔦 Увімк"),
            KeyboardButton(text="🌑 Вимк")
        )
        # 2 ряд: Календар, Погода, Новини
        builder.row(
            KeyboardButton(text="📄 Погода"),
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="📰 Новини")
        )
        # 3 ряд: Рестарти системні
        builder.row(
            KeyboardButton(text="🔄 Кіт"),
            KeyboardButton(text="🔄 SSH"),
            KeyboardButton(text="🔄 Тунель")
        )
        # 4 ряд: Рестарти ботів + Пам'ять
        builder.row(
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Дживс"),
            KeyboardButton(text="💾 Пам'ять")
        )
        # 5 ряд: Логи, Знайти телефон
        builder.row(
            KeyboardButton(text="📢 Знайти телефон"),
            KeyboardButton(text="📄 Логи"),
            KeyboardButton(text="❌ Еrror log")

        )
        # 6 ряд: Додати подію
        builder.row(
            KeyboardButton(text="➕ Додати подію"),
            #KeyboardButton(text="🗑 Видалити подію")
        )

    # --- АДМІНИ (ті, хто не власник, але є в списку) ---
    elif user_id in ADMIN_IDS:
        # 1 ряд: Календар, Погода, Новини
        builder.row(
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="🌦 Погода"),
            KeyboardButton(text="📰 Новини")
        )
        # 2 ряд: Рестарти (безпечні)
        builder.row(
            KeyboardButton(text="📢 Знайти телефон"),
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Кіт")
        )
        # 3 ряд: Додати подію
        builder.row(
            KeyboardButton(text="➕ Додати подію"),
            #KeyboardButton(text="🗑 Видалити подію")
        )

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
