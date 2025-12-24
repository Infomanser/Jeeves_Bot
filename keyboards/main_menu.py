from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(is_owner: bool = False, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Генерує нижнє меню (Reply Keyboard) залежно від прав доступу.
    """
    builder = ReplyKeyboardBuilder()

    # 1. РЯД: Lifestyle (Для Адмінів та Власника)
    if is_admin or is_owner:
        builder.row(
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="🌦 Погода"),
            KeyboardButton(text="📰 Новини")
        )

    # 2. РЯД: Hardware (Тільки для Власника)
    if is_owner:
        builder.row(
            KeyboardButton(text="🔦 Вкл"),
            KeyboardButton(text="🌑 Викл"),
            KeyboardButton(text="📊 Статус")
        )
        # 3. РЯД: Рестарти
        builder.row(
            KeyboardButton(text="🐈 перезапуск."),
            KeyboardButton(text="Рестарт 😈 SSH"),
            KeyboardButton(text="Рестарт головного 😈")
        )

    # Налаштування: кнопки компактні, меню не зникає
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
