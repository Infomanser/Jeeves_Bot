# keyboards/builders.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import OWNER_ID, ADMIN_IDS

def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    """
    Генерує меню залежно від прав користувача.
    """
    builder = ReplyKeyboardBuilder()

    # --- ЛОГІКА ДЛЯ ВЛАСНИКА (OWNER_ID) ---
    if user_id == OWNER_ID:
        # 1 ряд: Статус, Календар, Новини
        builder.row(
            KeyboardButton(text="📲 Статус"),
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="📰 Новини")
        )
        # 2 ряд: "Знайти телефон", Ліхтар увімк/вимк
        builder.row(
            KeyboardButton(text="📢 Знайти телефон"),
            KeyboardButton(text="🔦 Увімк"),
            KeyboardButton(text="🌑 Вимк")
        )
        # 3 ряд: Рестарти (Кіт, SSH, Тунель)
        builder.row(
            KeyboardButton(text="🔄 Кіт"),
            KeyboardButton(text="🔄 SSH"),
            KeyboardButton(text="🔄 Тунель")
        )
        # 4 ряд: Рестарти (Музика, Дживс, Пам'ять)
        builder.row(
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Дживс"),
            KeyboardButton(text="💾 Пам'ять")
        )
        # 5 ряд: Логи, Помилки
        builder.row(
            KeyboardButton(text="📄 Логи"),
            KeyboardButton(text="❌ Еrror log")
        )

    # --- ЛОГІКА ДЛЯ АДМІНІВ (ADMIN_IDS) ---
    elif user_id in ADMIN_IDS:
        # 1 ряд: Календар, Погода, Новини
        builder.row(
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="🌦 Погода"),
            KeyboardButton(text="📰 Новини")
        )
        # 2 ряд: Рестарти (Безпечні) + Знайти телефон (через команду, або кнопкою)
        builder.row(
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Кіт")
        )

    # --- ВСІ ІНШІ ---
    else:
        # Повертаємо None або пусту клавіатуру, щоб їм нічого не показувало
        return None

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
