# main.py
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TOKEN, LOG_FILE, OWNER_ID
from handlers import common, hardware, lifestyle, public
from utils.logger import setup_logging

# СЕРВІСИ ДЛЯ ЗВІТІВ
from services import termux_api as hardware_service
from services.calendar_api import check_upcoming_events
from services.weather_api import get_weather_forecast
from services.news_api import get_fresh_news

# --- СИСТЕМНИЙ РЕПОРТ (Кожні 4 години: 00, 04, 08...) ---
async def scheduled_reporter(bot: Bot):
    target_hours = [0, 4, 8, 12, 16, 20]
    while True:
        now = datetime.now()
        if now.hour in target_hours and now.minute == 0:
            try:
                report = hardware_service.get_full_system_report()
                await bot.send_message(OWNER_ID, f"🕰 <b>System ({now.strftime('%H:%M')}):</b>\n{report}")
                await asyncio.sleep(65)
            except Exception as e:
                logging.error(f"Reporter error: {e}")
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

# --- РАНКОВИЙ БРИФІНГ (09:00) ---
async def morning_briefing(bot: Bot):
    """
    Щоранку о 09:00:
    1. Свята/Події (якщо є)
    2. Погода
    3. Новини
    """
    while True:
        now = datetime.now()
        
        # Час брифінгу: 09:00
        if now.hour == 9 and now.minute == 0:
            try:
                parts = []
                
                # 1. КАЛЕНДАР
                events_text = check_upcoming_events()
                if events_text:
                    parts.append(f"📅 <b>Нагадування:</b>\n{events_text}")
                
                # 2. ПОГОДА
                # get_weather_forecast повертає готовий текст
                weather_text = await get_weather_forecast()
                if weather_text:
                    parts.append(f"{weather_text}")

                # 3. НОВИНИ
                news_text = await get_fresh_news()
                if news_text:
                    parts.append(f"{news_text}")

                # ВІДПРАВКА
                if parts:
                    # Можна відправити одним великим повідомленням (розділивши лінією)
                    full_text = "\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n".join(parts)
                    await bot.send_message(OWNER_ID, f"☕️ <b>Ранковий брифінг:</b>\n\n{full_text}", disable_web_page_preview=True)
                else:
                    # Якщо раптом все зламалось і пусто - хоч привітаємось
                    await bot.send_message(OWNER_ID, "☕️ Доброго ранку! Новин та подій немає.")

                await asyncio.sleep(65)
            except Exception as e:
                logging.error(f"Morning briefing error: {e}")
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

async def on_startup(bot: Bot):
    try:
        await bot.send_message(OWNER_ID, "🤖 <b>Jeeves Online!</b>")
    except: pass

async def main():
    setup_logging(LOG_FILE)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(hardware.router)
    dp.include_router(lifestyle.router)
    dp.include_router(public.router)

    # ЗАПУСК ФОНОВИХ ЗАДАЧ
    asyncio.create_task(scheduled_reporter(bot))
    asyncio.create_task(morning_briefing(bot))

    await on_startup(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
