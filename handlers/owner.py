from aiogram import Router, types
from aiogram.filters import Command
from utils.filters import IsOwner
# import services.termux_api as termux

# Створюємо роутер і одразу кажемо: сюди пускати ТІЛЬКИ власника
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
