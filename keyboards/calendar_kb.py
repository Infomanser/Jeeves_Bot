# keyboards/calendar_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_events_filter_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Всі події" на всю ширину
    builder.row(
        InlineKeyboardButton(text="📋 Показати всі події", callback_data="cal_all")
    )

    # Сезони по 2 в ряд
    builder.row(
        InlineKeyboardButton(text="❄️ Зима", callback_data="cal_winter"),
        InlineKeyboardButton(text="🌱 Весна", callback_data="cal_spring")
    )
    builder.row(
        InlineKeyboardButton(text="☀️ Літо", callback_data="cal_summer"),
        InlineKeyboardButton(text="🍂 Осінь", callback_data="cal_autumn")
    )
    
    return builder.as_markup()

def get_edit_kb(event_id: int) -> InlineKeyboardMarkup:
    """Кнопки під конкретною подією (Редагувати / Видалити)"""

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Ред.", callback_data=f"edit_evt_{event_id}")
    )
    return builder.as_markup()
