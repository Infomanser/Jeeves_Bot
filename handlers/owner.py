from aiogram import Bot, Router, types
from aiogram.filters import Command
from config import OWNER_ID
from datetime import datetime
from services.calendar_api import check_upcoming_events
from services.weather_api import get_weather_forecast
from services.news_api import get_fresh_news
from services.fitness import get_today_workout
from utils.filters import IsOwner

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
    await message.answer("☕️ Генерую тестовий брифінг...")
    
    try:
        now = datetime.now() # Визначення поточної дати
        parts = []
        if now.weekday() == 6:
            try:
                from services.weather_api import get_weekly_forecast
                weekly_weather = await get_weekly_forecast()
                await message.answer(weekly_weather)
            except Exception as e:
                logging.error(f"Weekly weather error: {e}")

        # 2. КАЛЕНДАР
        events_text = check_upcoming_events(OWNER_ID)
        if events_text:
            parts.append(f"📅 <b>Нагадування:</b>\n{events_text}")
        
        # 3. ПОГОДА (Поточна)
        weather_text = await get_weather_forecast()
        if weather_text:
            parts.append(f"{weather_text}")

        # 4. НОВИНИ
        news_text = await get_fresh_news()
        if news_text:
            parts.append(f"🗞 <b>Свіжа преса:</b>\n\n{news_text}")

        # 5. ФІТНЕС
        fitness_text = await get_today_workout()
        if fitness_text:
            parts.append(fitness_text)

        # ФОРМУВАННЯ ФІНАЛЬНОГО БРИФІНГУ
        if parts:
            full_text = "\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n".join(parts)
            await message.answer(
                f"☕️ <b>Ранковий брифінг (TEST):</b>\n\n{full_text}", 
                disable_web_page_preview=True
            )
        else:
            await message.answer("☕️ Новин та подій немає.")
            
    except Exception as e:
        logging.error(f"Briefing command error: {e}")
        await message.answer(f"❌ Помилка при генерації: {e}")
