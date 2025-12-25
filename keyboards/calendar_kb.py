# keyboards/calendar_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_events_filter_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # 1 ряд: Сьогодні і Тиждень
    builder.row(
        InlineKeyboardButton(text="🔥 Сьогодні", callback_data="cal_today"),
        InlineKeyboardButton(text="👀 Тиждень", callback_data="cal_week")
    )
    # 2 ряд: Місяць і Всі
    builder.row(
        InlineKeyboardButton(text="📅 Місяць", callback_data="cal_month"),
        InlineKeyboardButton(text="📋 Всі події", callback_data="cal_all")
    )
    
    return builder.as_markup()

def get_edit_kb(event_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Ред.", callback_data=f"edit_evt_{event_id}")
    )
    return builder.as_markup()
