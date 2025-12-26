# handlers/admin.py
import sqlite3
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command
from utils.filters import IsAdmin

# Сюди пускаємо всіх зі списку ADMIN_IDS
router = Router()
router.message.filter(IsAdmin()) 

@router.message(Command("add_event"))
async def cmd_add_event(message: types.Message):
    await message.answer("📅 Додаємо подію...")
