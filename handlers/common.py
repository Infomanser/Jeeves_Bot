# handlers/common.py
import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.weather_api import get_weekly_forecast

router = Router()

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("🤷‍♂️ Немає чого скасовувати.")
        return
    await state.clear()
    await message.answer("👌 Скасовано.")

@router.message(Command("weekly"))
@router.message(F.text.in_({"🌦 Погода на тиждень", "Погода на тиждень"}))
async def cmd_weekly_public(message: types.Message):
    status_msg = await message.answer("📅 Отримую прогноз на тиждень...")
    try:
        from services.weather_api import get_weekly_forecast
        text = await get_weekly_forecast()
        await status_msg.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Public weekly error: {e}")
        await status_msg.edit_text("❌ Не вдалося отримати прогноз.")
