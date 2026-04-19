from aiogram import Router, types
from aiogram.filters import Command
from utils.filters import IsOwner
# import services.termux_api as termux
from aiogram import Bot
from config import OWNER_ID
from services.calendar_api import check_upcoming_events
from services.weather_api import get_weather_forecast
from services.news_api import get_fresh_news
from services.fitness import get_today_workout

router = Router()
router.message.filter(IsOwner()) 

@router.message(Command("reboot"))
async def cmd_reboot(message: types.Message):
    await message.answer("🔄 Перезавантажуюсь...")
    # логіка ребуту

@router.message(Command("say"))
async def cmd_say(message: types.Message):
    # termux.speak(...)
    await message.answer("🗣 Кажу...")

@router.message(Command('brief'))
async def cmd_briefing(message: types.Message, bot: Bot):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("☕️ Генерую тестовий брифінг...")
    
    try:
        parts = []

        if now.weekday() == 6:
            weekly_weather = await get_weekly_forecast()
            await bot.send_message(OWNER_ID, weekly_weather)

        events_text = check_upcoming_events(OWNER_ID)
        if events_text:
            parts.append(f"📅 <b>Нагадування:</b>\n{events_text}")
        
        weather_text = await get_weather_forecast()
        if weather_text:
            parts.append(f"{weather_text}")

        news_text = await get_fresh_news()
        if news_text:
            parts.append(f"{news_text}")

        fitness_text = await get_today_workout()
        if fitness_text:
            parts.append(f"{fitness_text}")

        if parts:
            full_text = "\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n".join(parts)
            await message.answer(f"☕️ <b>Ранковий брифінг (TEST):</b>\n\n{full_text}", disable_web_page_preview=True)
        else:
            await message.answer("☕️ Новин та подій немає.")
            
    except Exception as e:
        await message.answer(f"❌ Помилка при генерації: {e}")
