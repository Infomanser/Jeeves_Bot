import html
import subprocess
import os
import glob
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject

from config import OWNER_ID, ADMIN_IDS
from services import termux_api as hardware
from services.db_manager import backup_database

router = Router()

# --- ХЕЛПЕРИ ПРАВ ---
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMIN_IDS

# --- 1. СТАТУС ---

@router.message(Command("status"))
@router.message(F.text == "📲 Статус")
async def cmd_status(message: types.Message):
    if not is_owner(message.from_user.id): return
    
    await message.answer("🔍 Збираю дані про систему...")
    report = hardware.get_full_system_report()
    
    if len(report) > 4096: 
        report = report[:4090] + "..."
    await message.answer(report)

# --- 2. ЛІХТАР (Тільки Власник) ---

@router.message(F.text == "🔦 Увімк")
async def cmd_light_on(message: types.Message):
    if not is_owner(message.from_user.id): return
    hardware.torch('on')
    await message.answer("🔦 Ліхтар увімкнено.")

@router.message(F.text == "🌑 Вимк")
async def cmd_light_off(message: types.Message):
    if not is_owner(message.from_user.id): return
    hardware.torch('off')
    await message.answer("🌑 Ліхтар вимкнено.")

# --- 3. TTS (ЗНАЙТИ ТЕЛЕФОН) ---

@router.message(F.text == "📢 Знайти телефон")
async def btn_find_phone(message: types.Message):
    if not is_owner(message.from_user.id): return
    
    await message.answer("📣 <b>УВАГА!</b> Вмикаю сирену!")
    hardware.tts_speak("Увага! Я тут! Зверни на мене увагу! " * 5)

@router.message(Command("say"))
async def cmd_say(message: types.Message, command: CommandObject):
    if not is_admin(message.from_user.id): return

    if not command.args:
        return await message.answer("🗣 Напиши: <code>/say Текст</code>")
    
    hardware.tts_speak(command.args)
    await message.answer(f"🗣 Кажу: <i>{html.escape(command.args)}</i>")

# --- 4. РЕСТАРТИ СЕРВІСІВ (PM2) ---

SERVICES_MAP = {
    "🔄 AllSaver": "allssaverbot",
    "🔄 Кіт": "misanthrope_cat",
    "🔄 Тунель": "moto",
    "🔄 SSH": "ssh-server",
    "🔄 Дживс": "Jeeves"
}

RESTRICTED_SERVICES = ["moto", "ssh-server", "Jeeves"]

@router.message(F.text.startswith("🔄 "))
async def handle_restarts(message: types.Message):
    user_id = message.from_user.id
    if not is_admin(user_id): return

    service_name = SERVICES_MAP.get(message.text)
    
    if not service_name:
        return await message.answer(f"❓ Не знайшов сервіс для кнопки '{message.text}'")

    if service_name in RESTRICTED_SERVICES and not is_owner(user_id):
        return await message.answer("⛔️ Цей сервіс дозволено перезапускати тільки Власнику.")

    await message.answer(f"⏳ Перезапускаю <b>{service_name}</b>...")

    if service_name == "Jeeves":
        await message.answer("♻️ Йду на перезавантаження. Побачимось за мить! 👋")
    
    try:
        subprocess.run(["pm2", "restart", service_name], check=True)
        if service_name != "Jeeves":
            await message.answer(f"✅ {message.text}: Успішно!")
    except subprocess.CalledProcessError:
        await message.answer(f"❌ {message.text}: Помилка PM2.")

# --- 5. ЛОГИ (Тільки Власник) ---

@router.message(F.text == "📄 Логи")
@router.message(F.text == "Логи")
async def cmd_logs(message: types.Message):
    if not is_owner(message.from_user.id): return
    
    await message.answer("📋 Читаю останні 20 рядків логів...")
    try:
        result = subprocess.check_output(
            ["pm2", "logs", "--lines", "20", "--nostream", "--raw"], 
            stderr=subprocess.STDOUT
        ).decode('utf-8')
        
        clean_logs = html.escape(result[-3500:]) 
        await message.answer(f"<pre>{clean_logs}</pre>")
    except Exception as e:
        await message.answer(f"❌ Не вдалося отримати логи: {e}")

@router.message(F.text == "❌ Еrror log")
async def cmd_err_logs(message: types.Message):
    if not is_owner(message.from_user.id): return
    
    home_dir = os.path.expanduser("~")
    pm2_log_dir = os.path.join(home_dir, ".pm2", "logs")
    
    main_error_log = os.path.join(pm2_log_dir, "Jeeves-error.log")
    
    target_file = main_error_log
    info_msg = "📋 Логи помилок (Active):"

    if os.path.exists(main_error_log) and os.path.getsize(main_error_log) == 0:
        search_pattern = os.path.join(pm2_log_dir, "Jeeves-error__*.log")
        rotated_files = sorted(glob.glob(search_pattern))
        
        if rotated_files:
            target_file = rotated_files[-1]
            info_msg = f"📋 Лог пустий. Читаю архів:\n{os.path.basename(target_file)}"
        else:
             return await message.answer("✅ Файл помилок пустий і архівів немає. (Clean run)")
    
    await message.answer(info_msg)

    try:
        output = subprocess.check_output(["tail", "-n", "30", target_file]).decode("utf-8")
        
        if output.strip():
            await message.answer(f"<pre>{html.escape(output)}</pre>")
        else:
            await message.answer("✅ Лог пустий.")
            
    except Exception as e:
        await message.answer(f"❌ Помилка читання файлу: {e}")

# --- 6. РЕЗЕРВНЕ КОПІЮВАННЯ БД (Тільки Власник) ---
@router.message(F.text == "💾 Бекап БД")
async def force_backup(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    status, result = backup_database()
    if status:
        await message.answer(f"✅ **Бекап створено!**\n📂 `{result}`", parse_mode="Markdown")
    else:
        await message.answer(f"❌ **Помилка:** {result}")