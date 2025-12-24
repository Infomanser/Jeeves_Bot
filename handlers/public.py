# handlers/public.py
import html # <--- ДОДАНО
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from utils.filters import IsOwner, IsAdmin
from utils.helpers import get_time_greeting
from keyboards.main_menu import get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    name = html.escape(message.from_user.first_name)
    greeting = get_time_greeting()
    
    # Визначаємо права для побудови меню
    # (Викликаємо фільтри вручну, щоб отримати True/False)
    _is_owner = await IsOwner()(message)
    _is_admin = await IsAdmin()(message)

    # Генеруємо меню
    menu_kb = get_main_menu(is_owner=_is_owner, is_admin=_is_admin)
    
    # 1. ВЛАСНИК
    if _is_owner:
        await message.answer(
            f"{greeting}, Шеф {hbold(name)}! 🎩\n"
            f"Системи в нормі. Чекаю на вказівки.\n\n"
            f"🔧 <b>Доступні команди:</b>\n"
            f"/status - Стан системи\n"
            f"/light_on - Ліхтар\n"
            f"/reboot - Перезавантаження",
            reply_markup=menu_kb # <--- ДОДАНО: Показуємо кнопки
        )
    
    # 2. АДМІН
    elif _is_admin:
        await message.answer(
            f"{greeting}, {hbold(name)}! 👋\n"
            f"Я готовий допомагати.",
            reply_markup=menu_kb # <--- ДОДАНО
        )
        
    # 3. ЧУЖИЙ
    else:
        await message.answer(
            f"Вітаю, {name}.\n"
            f"Я приватний асистент. У мене немає функцій для публічного доступу.\n"
            f"Гарного дня! 🤖"
        )

@router.message(Command("id"))
async def cmd_id(message: types.Message):
    await message.answer(f"🆔 Твій Telegram ID: <code>{message.from_user.id}</code>")
