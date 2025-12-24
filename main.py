# main.py
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Імпорти конфігу
from config import TOKEN, LOG_FILE, OWNER_ID

# Імпорти роутерів
from handlers import common, lifestyle, hardware, public
from utils.logger import setup_logging

# Імпорт для звіту
from services import termux_api as hardware_service

async def scheduled_reporter(bot: Bot):
    """
    Фоновий демон, який слідкує за часом і шле звіти.
    Графік: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00.
    """
    target_hours = [0, 4, 8, 12, 16, 20]
    
    while True:
        now = datetime.now()
        
        # Перевіряємо, чи зараз "рівна" година зі списку і чи це початок години (0 хвилин)
        if now.hour in target_hours and now.minute == 0:
            try:
                report = hardware_service.get_full_system_report()
                await bot.send_message(
                    OWNER_ID, 
                    f"🕰 <b>Плановий звіт ({now.strftime('%H:%M')}):</b>\n{report}",
                    parse_mode=ParseMode.HTML
                )
                # Чекаємо 61 секунду, щоб не відправити двічі за одну хвилину
                await asyncio.sleep(61)
            except Exception as e:
                logging.error(f"Reporter error: {e}")
                await asyncio.sleep(60)
        else:
            # Спимо 30 секунд перед наступною перевіркою
            await asyncio.sleep(30)

async def main():
    setup_logging(LOG_FILE)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Реєстрація роутерів (Hardware для власника - перший!)
    dp.include_router(hardware.router)
    dp.include_router(lifestyle.router)
    dp.include_router(public.router)
    # dp.include_router(common.router) # Якщо він порожній або дублює public - можна прибрати

    # ЗАПУСК ФОНОВОГО ЗАВДАННЯ
    asyncio.create_task(scheduled_reporter(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
