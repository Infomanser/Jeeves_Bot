# handlers/public.py
import html
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

# Імпорти конфігурації
from config import OWNER_ID, ADMIN_IDS
from keyboards.builders import get_main_menu
from utils.helpers import get_time_greeting

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    name = html.escape(message.from_user.first_name)
    greeting = get_time_greeting()
    
    # Визначаємо статус для тексту
    is_owner = (user_id == OWNER_ID)
    is_admin = (user_id in ADMIN_IDS) or is_owner


    menu_kb = get_main_menu(user_id)
    
    # 1. ВЛАСНИК
    if is_owner:
        await message.answer(
            f"{greeting}, Шеф {hbold(name)}! 🎩\n"
            f"Системи в нормі. Чекаю на вказівки.",
            reply_markup=menu_kb
        )
    
    # 2. АДМІН
    elif is_admin:
        await message.answer(
            f"{greeting}, {hbold(name)}! 👋\n"
            f"Радий бачити. Ось твій пульт.",
            reply_markup=menu_kb
        )
        
    # 3. ЧУЖИЙ
    else:
        await message.answer(
            f"Вітаю, {name}.\n"
            f"Я приватний асистент Jeeves. У мене немає функцій для публічного доступу.\n"
            f"Гарного дня! 🤖"
        )

@router.message(Command("id"))
async def cmd_id(message: types.Message):
    await message.answer(f"🆔 Твій Telegram ID: <code>{message.from_user.id}</code>")
