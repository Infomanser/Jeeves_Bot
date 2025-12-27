# handlers/navigation.py
from aiogram import Router, F
from aiogram.types import Message
from config import OWNER_ID
from keyboards.builders import (
    get_main_menu, 
    get_restarts_menu, 
    get_tools_menu, 
    get_info_menu
)

router = Router()

# --- ВХІД У ПАПКИ ---

@router.message(F.text == "🔄 Керування")
async def open_restarts(message: Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("🔄 <b>Меню рестартів:</b>", reply_markup=get_restarts_menu(), parse_mode="HTML")

@router.message(F.text == "🛠 Інструменти")
async def open_tools(message: Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("🛠 <b>Інструменти та діагностика:</b>", reply_markup=get_tools_menu(), parse_mode="HTML")

@router.message(F.text == "📂 Інфо")
async def open_info(message: Message):
    if message.from_user.id == OWNER_ID:
        await message.answer("📂 <b>Інформаційний розділ:</b>", reply_markup=get_info_menu(), parse_mode="HTML")

# --- ВИХІД (НАЗАД) ---

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    # Повертаємо головне меню
    menu = get_main_menu(message.from_user.id)
    if menu:
        await message.answer("🏡 <b>Головне меню:</b>", reply_markup=menu, parse_mode="HTML")
    else:
        await message.answer("🚫 Доступу немає.", reply_markup=None)