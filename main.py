# main.py
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Конфіг
from config import TOKEN, LOG_FILE, OWNER_ID

# Роутери
from handlers import common, hardware, lifestyle, public
from utils.logger import setup_logging
from services import termux_api as hardware_service

async def scheduled_reporter(bot: Bot):
    """
    Звітує о 00:00, 04:00, 08:00, 12:00, 16:00, 20:00.
    """
    target_hours = [0, 4, 8, 12, 16, 20]
    
    while True:
        now = datetime.now()
        
        if now.hour in target_hours and now.minute == 0:
            try:
                report = hardware_service.get_full_system_report()
                await bot.send_message(
                    OWNER_ID, 
                    f"🕰 <b>Плановий звіт ({now.strftime('%H:%M')}):</b>\n{report}",
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(65)
            except Exception as e:
                logging.error(f"Reporter error: {e}")
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

async def on_startup(bot: Bot):
    try:
        await bot.send_message(OWNER_ID, "🤖 <b>Jeeves Online!</b>\nЯ перезавантажився і готовий до роботи.")
    except Exception as e:
        logging.error(f"Startup msg failed: {e}")

async def main():
    setup_logging(LOG_FILE)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # --- ПОРЯДОК РОУТЕРІВ ---
    
    # 1. Common (Cancel має пріоритет, щоб вийти з будь-якого стану)
    dp.include_router(common.router)
    
    # 2. Hardware (Критичні команди, рестарти, ліхтар)
    dp.include_router(hardware.router)
    
    # 3. Lifestyle (Основна логіка: календар, погода)
    dp.include_router(lifestyle.router)
    
    # 4. Public (Start, ID і все, що не спіймали інші)
    dp.include_router(public.router)

    # Запуск фонових задач
    asyncio.create_task(scheduled_reporter(bot))
    await on_startup(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
