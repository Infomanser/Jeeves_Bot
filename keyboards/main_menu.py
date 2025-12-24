from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import OWNER_ID, ADMIN_IDS

def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    """
    Генерує меню на основі ID користувача.
    Власник отримує повний пульт керування (5 рядів).
    Адміни отримують базовий набір (2 ряди).
    Ліві юзери не отримують нічого.
    """
    builder = ReplyKeyboardBuilder()

    # --- ВЛАСНИК ---
    if user_id == OWNER_ID:
        # 1 ряд: Статус, Календар, Новини
        builder.row(
            KeyboardButton(text="📲 Статус"),
            KeyboardButton(text="📅 Календар"),
            KeyboardButton(text="📰 Новини")
        )
        # 2 ряд: "Знайти телефон", Ліхтар
        builder.row(
            KeyboardButton(text="📢 Знайти телефон"),
            KeyboardButton(text="🔦 Увімк"),
            KeyboardButton(text="🌑 Вимк")
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
        # 5 ряд: Логи
        builder.row(
            KeyboardButton(text="📄 Логи"),
            KeyboardButton(text="❌ Еrror log")
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
            KeyboardButton(text="🔄 AllSaver"),
            KeyboardButton(text="🔄 Кіт")
        )

    # Якщо юзера немає ніде — повернеться пуста клавіатура (або None, якщо перевірка в хендлері)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
