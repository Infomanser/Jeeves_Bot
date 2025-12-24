# handlers/hardware.py
import html
from aiogram import Router, types, F # <--- ДОДАНО F
from aiogram.filters import Command, CommandObject
from utils.filters import IsOwner
from services import termux_api as hardware

router = Router()
router.message.filter(IsOwner())

# --- Інформаційні команди ---

@router.message(Command("status"))
@router.message(F.text == "📊 Статус")
async def cmd_status(message: types.Message):
    await message.answer("🔍 Збираю дані про систему...")
    report = hardware.get_full_system_report()
    if len(report) > 4096: 
        report = report[:4090] + "..."
    await message.answer(report)

@router.message(Command("storage"))
async def cmd_storage(message: types.Message):
    info = hardware.get_storage_info()
    await message.answer(f"💾 <b>Сховище:</b>\n{info}")

@router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer(f"🏓 Pong! Аптайм: {hardware.get_uptime()}")

# --- Управління залізом ---

@router.message(Command("light_on"))
@router.message(F.text == "🔦 Вкл")
async def cmd_light_on(message: types.Message):
    hardware.torch_control('on')
    await message.answer("🔦 Ліхтар увімкнено.")

@router.message(Command("light_off"))
@router.message(F.text == "🌑 Викл") # <--- Додав текст кнопки
async def cmd_light_off(message: types.Message):
    hardware.torch_control('off')
    await message.answer("🌑 Ліхтар вимкнено.")

@router.message(Command("say"))
async def cmd_say(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("🗣 Напиши, що сказати. Наприклад: <code>/say Привіт</code>")
    hardware.speak_text(command.args)
    await message.answer(f"🗣 Промовляю: <i>{html.escape(command.args)}</i>")

# --- Перезавантаження сервісів (PM2) ---

async def _restart_helper(message: types.Message, service_name: str, friendly_name: str):
    await message.answer(f"🔄 Перезапускаю <b>{friendly_name}</b>...")
    if hardware.restart_pm2_service(service_name):
        await message.answer(f"✅ {friendly_name}: Успішно!")
    else:
        await message.answer(f"❌ {friendly_name}: Помилка PM2.")

@router.message(Command("r_cat"))
@router.message(F.text == "🐈 перезапуск.")
async def restart_cat(message: types.Message):
    await _restart_helper(message, "misanthrope_cat", "Кота")

@router.message(Command("r_ssh"))
@router.message(F.text == "Рестарт 😈 SSH")
async def restart_ssh(message: types.Message):
    await _restart_helper(message, "ssh-server", "SSH")

@router.message(Command("r_status", "reboot"))
@router.message(F.text == "Рестарт головного 😈")
async def restart_bot(message: types.Message):
    await message.answer("♻️ Перезавантажуюсь... Побачимось за мить! 👋")
    hardware.restart_pm2_service("status")
