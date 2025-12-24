# keyboards/builders.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(is_owner: bool = False, is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # РЯД 1: Загальне (Адмін + Власник)
    if is_admin or is_owner:
        builder.row(
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="🌦 Погода"),
            KeyboardButton(text="📰 Новини")
        )

    # РЯД 2: Хардвар (Тільки Власник)
    if is_owner:
        builder.row(
            KeyboardButton(text="🔦 Вкл"),
            KeyboardButton(text="🌑 Викл"),
            KeyboardButton(text="📊 Статус")
        )
        # РЯД 3: Рестарти
        builder.row(
            KeyboardButton(text="🐈 перезапуск."),
            KeyboardButton(text="Рестарт 😈 SSH"),
            KeyboardButton(text="Рестарт головного 😈")
        )

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
