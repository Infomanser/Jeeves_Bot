# Jeeves_Bot/keyboards/calendar_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_events_filter_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Сьогодні", callback_data="cal_today")
    builder.button(text="🗓 Тиждень", callback_data="cal_week")
    builder.button(text="📆 Місяць", callback_data="cal_month")
    builder.button(text="📚 Всі", callback_data="cal_all")
    builder.adjust(2) # По 2 кнопки в ряд
    return builder.as_markup()

def get_edit_kb(event_id: int):
    """Кнопка редагування під конкретним івентом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"edit_evt_{event_id}")]
    ])
