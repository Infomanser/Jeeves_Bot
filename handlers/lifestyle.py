# handlers/lifestyle.py
import html
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

# Імпорти конфігурації
from config import OWNER_ID, ADMIN_IDS

# Сервіси
from services.calendar_api import (
    get_events, 
    mass_import_events, 
    get_event_by_id, 
    update_event_text, 
    add_new_event, 
    decode_event_to_string,
    delete_event,
    check_upcoming_events
)
from keyboards.calendar_kb import get_events_filter_kb, get_edit_kb
from services.weather_api import get_weather_forecast, search_city, set_city_coords 
from services.news_api import get_fresh_news

router = Router()

# --- STATES ---
class CalendarStates(StatesGroup):
    waiting_for_import = State()
    waiting_for_edit_text = State()

class AddEvent(StatesGroup):
    waiting_for_date = State()
    waiting_for_name = State()
    waiting_for_link = State()

class WeatherStates(StatesGroup):
    waiting_for_city = State()

# --- HELPER ---
def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMIN_IDS

# --- WEATHER & NEWS ---

@router.message(Command("set_city"))
async def cmd_set_city(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id): return
    
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        city_name = args[1]
        await find_and_save_city(message, city_name)
    else:
        await message.answer("🏙 Введіть назву міста для пошуку:")
        await state.set_state(WeatherStates.waiting_for_city)

@router.message(Command("weather"))
@router.message(F.text == "🌦 Погода")
async def cmd_weather(message: types.Message):
    if not is_authorized(message.from_user.id): return

    sent_msg = await message.answer("🌤 Дивлюсь у вікно...")
    text = await get_weather_forecast()
    await sent_msg.edit_text(text)

@router.message(WeatherStates.waiting_for_city)
async def process_city_input(message: types.Message, state: FSMContext):
    await find_and_save_city(message, message.text)
    await state.clear()

async def find_and_save_city(message: types.Message, city_name: str):
    msg = await message.answer(f"🔎 Шукаю <b>{html.escape(city_name)}</b>...")
    result = await search_city(city_name)
    
    if result:
        set_city_coords(result['name'], result['lat'], result['lon'])
        country = f"({result['country']})" if result['country'] else ""
        await msg.edit_text(
            f"✅ Місто змінено на <b>{result['name']}</b> {country}.\n"
            f"Тепер команда /weather показуватиме погоду тут."
        )
    else:
        await msg.edit_text("❌ Місто не знайдено.")

@router.message(Command("news"))
@router.message(F.text == "📰 Новини")
async def cmd_news(message: types.Message):
    if not is_authorized(message.from_user.id): return

    sent_msg = await message.answer("📰 Гортаю газети...")
    text = await get_fresh_news()
    await sent_msg.edit_text(text, disable_web_page_preview=True)

# --- 1. ПЕРЕГЛЯД КАЛЕНДАРЯ ---

@router.message(Command("events"))
@router.message(F.text == "📅 Календар")
async def cmd_events(message: types.Message):
    if not is_authorized(message.from_user.id): return
    await message.answer("📅 <b>Оберіть період:</b>", reply_markup=get_events_filter_kb())

@router.callback_query(F.data.startswith("cal_"))
async def process_filter(callback: types.CallbackQuery):
    filter_type = callback.data.split("_")[1]
    events = get_events(filter_type)
    
    if not events:
        await callback.message.edit_text("🤷‍♂️ Подій у цьому діапазоні немає.", reply_markup=get_events_filter_kb())
        return

    await callback.message.delete()
    
    for event in events:
        text_display = f"<b>{event['date']}</b>: {decode_event_to_string(event)}"
        await callback.message.answer(text_display, reply_markup=get_edit_kb(event['id']), disable_web_page_preview=True)

    await callback.message.answer("🔽 Меню:", reply_markup=get_events_filter_kb())

# --- 2. МАСОВИЙ ІМПОРТ ---
@router.message(Command("import"))
async def cmd_import(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id): return
    await message.answer(
        "📦 <b>Масовий імпорт</b>\n"
        "Формат:\n<pre>14.02 День Валентина\n08.03 Жіночий день</pre>"
    )
    await state.set_state(CalendarStates.waiting_for_import)

@router.message(CalendarStates.waiting_for_import)
async def process_import(message: types.Message, state: FSMContext):
    count = mass_import_events(message.text)
    await message.answer(f"✅ Успішно додано подій: {count}")
    await state.clear()

# --- 3. РЕДАГУВАННЯ ---
@router.callback_query(F.data.startswith("edit_evt_"))
async def start_edit(callback: types.CallbackQuery, state: FSMContext):
    evt_id = int(callback.data.split("_")[2])
    event = get_event_by_id(evt_id)
    if not event:
        return await callback.answer("⚠️ Подія не знайдена.", show_alert=True)

    await state.update_data(edit_id=evt_id)
    await callback.message.answer(
        f"📝 Редагуємо подію за <b>{event['date']}</b>.\nПоточний текст: <code>{event['text']}</code>\nВведіть новий:"
    )
    await state.set_state(CalendarStates.waiting_for_edit_text)

@router.message(CalendarStates.waiting_for_edit_text)
async def finish_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    evt_id = data.get('edit_id')
    if update_event_text(evt_id, message.text):
        await message.answer("✅ Зміни збережено.")
    else:
        await message.answer("❌ Помилка збереження.")
    await state.clear()

# --- 4. ДОДАВАННЯ ПОДІЇ (Wizard) ---
@router.message(Command("add"))
async def start_add_event(message: types.Message, state: FSMContext):
    if not is_authorized(message.from_user.id): return
    await message.answer("📅 <b>Крок 1/3:</b> Введіть дату (наприклад, <code>14.02</code>):")
    await state.set_state(AddEvent.waiting_for_date)

@router.message(Command("del"))
async def cmd_delete_event(message: types.Message):
    if not is_authorized(message.from_user.id): return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("🗑 Використання: <code>/del 14.02</code> або <code>/del Назва</code>")
    
    query = args[1].strip()
    
    try:
        result = delete_event(query) 
        await message.answer(f"🗑 {result}")
    except Exception as e:
        await message.answer(f"❌ Помилка видалення: {e}")

@router.message(AddEvent.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if "." not in text or not any(char.isdigit() for char in text):
        return await message.answer("⚠️ Некоректний формат. Треба ДД.ММ")
    
    await state.update_data(date=text)
    await message.answer("📝 <b>Крок 2/3:</b> Назва події:")
    await state.set_state(AddEvent.waiting_for_name)

@router.message(AddEvent.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=html.escape(message.text.strip()))
    await message.answer("🔗 <b>Крок 3/3:</b> Посилання (або «-»):")
    await state.set_state(AddEvent.waiting_for_link)

@router.message(AddEvent.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    try:
        saved_event = add_new_event(
            date=user_data['date'], 
            name=user_data['name'], 
            raw_link=message.text.strip()
        )
        preview = decode_event_to_string(saved_event)
        await message.answer(f"✅ <b>Збережено!</b>\n📅 {saved_event['date']}: {preview}", disable_web_page_preview=True)
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}")
    await state.clear()

# --- ТЕСТ РАНКОВОГО ЗВІТУ ---
@router.message(Command("briefing"))
async def cmd_manual_briefing(message: types.Message):
    if not is_authorized(message.from_user.id): return

    status_msg = await message.answer("☕️ Збираю ранкову пресу...")

    parts = []

    # 1. КАЛЕНДАР
    events_text = check_upcoming_events()
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

    # ВІДПРАВКА
    if parts:
        full_text = "\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n".join(parts)
        await status_msg.edit_text(
            f"☕️ <b>Ранковий брифінг (Manual):</b>\n\n{full_text}", 
            disable_web_page_preview=True
        )
    else:
        await status_msg.edit_text("☕️ Доброго ранку! Новин та подій немає.")
