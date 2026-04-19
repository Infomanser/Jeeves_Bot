import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, LOG_FILE, OWNER_ID
from handlers import common, hardware, lifestyle, public, notes, navigation
from utils.logger import setup_logging

# СЕРВІСИ
from services import termux_api as hardware_service
from services.calendar_api import check_upcoming_events
from services.weather_api import get_weather_forecast
from services.news_api import get_fresh_news
from services.db_manager import init_db, backup_database
from services.fitness import get_hydration_reminder, get_today_workout 

# --- СИСТЕМНИЙ РЕПОРТ ---
async def scheduled_reporter(bot: Bot):
    target_hours = [0, 4, 8, 12, 16, 20]
    while True:
        now = datetime.now()
        if now.hour in target_hours and now.minute == 0:
            try:
                report = hardware_service.get_full_system_report()
                await bot.send_message(OWNER_ID, report)
                await asyncio.sleep(65)
            except Exception as e:
                logging.error(f"Reporter error: {e}")
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

# --- РАНКОВИЙ БРИФІНГ (09:00) ---
async def morning_briefing(bot: Bot):
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            try:
                parts = []
                
                # 1. КАЛЕНДАР
                events_text = check_upcoming_events(OWNER_ID)
                if events_text:
                    parts.append(f"📅 <b>Нагадування:</b>\n{events_text}")
                
                # 2. ПОГОДА
                weather_text = await get_weather_forecast()
                if weather_text:
                    parts.append(f"{weather_text}")

                # 3. НОВИНИ
                news_text = await get_fresh_news()
                if news_text:
                    parts.append(f"{news_text}")

                # 4. ФІТНЕС
                fitness_text = await get_today_workout()
                if fitness_text:
                    parts.append(f"{fitness_text}")

                if parts:
                    full_text = "\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n".join(parts)
                    await bot.send_message(OWNER_ID, f"☕️ <b>Ранковий брифінг:</b>\n\n{full_text}", disable_web_page_preview=True)
                else:
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

async def send_water_alert(bot: Bot):
    try:
        text = await get_hydration_reminder()
        await bot.send_message(chat_id=OWNER_ID, text=text)
    except Exception as e:
        logging.error(f"Water error: {e}")

async def main():
    try: os.system('termux-wake-lock')
    except: pass

    init_db()
    backup_database()
    setup_logging(LOG_FILE)
    
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(navigation.router)
    dp.include_router(common.router)
    dp.include_router(hardware.router)
    dp.include_router(lifestyle.router)
    dp.include_router(notes.router)
    dp.include_router(public.router)

    asyncio.create_task(scheduled_reporter(bot))
    asyncio.create_task(morning_briefing(bot))

    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(
        send_water_alert,
        'cron',
        hour='12,13,14,15,16,17,18,19,20,21,22,23,0',
        args=[bot]
    )
    scheduler.start()

    await on_startup(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    while True:
        try:
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            with open("crash_history.log", "a") as f:
                f.write(f"[{datetime.now()}] Polling Crash: {str(e)}\n")
            logging.error(f"Critical polling error: {e}")
            await asyncio.sleep(15)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
