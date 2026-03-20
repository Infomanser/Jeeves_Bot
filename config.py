# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

load_dotenv()

TOKEN = os.getenv('TOKEN')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OWNER_ID = int(os.getenv('OWNER_ID', 0))

raw_admin_ids = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in raw_admin_ids.split(',') if id.strip()]
if OWNER_ID not in ADMIN_IDS: ADMIN_IDS.append(OWNER_ID)

# Weather Defaults
DEFAULT_LAT = 51.4982
DEFAULT_LON = 31.2893
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Chernihiv')

# RSS Config
raw_feeds = os.getenv('RSS_FEEDS', '')
RSS_FEEDS = [url.strip() for url in raw_feeds.split(',') if url.strip()]

# Fitness activitys
FITNESS_PLAN = {
    0: (
        "🏗 <b>Понеділок: Upper Frame & Base (Ширина + Жим)</b>\n"
        "<i>Баланс тяги і жиму.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        
        "• 🧗‍♂️ <b>Підтягування + вага:</b> 4×6–10\n"
        "• 🧗‍♂️ <b>Підтягування без ваги:</b> 2×макс\n"
        
        "• 🤸‍♂️ <b>Віджимання + вага (рюкзак):</b> 4×10–15\n"
        
        "• 🔁 <b>Горизонтальна тяга:</b> 3×10–15\n"
        "(резинка / TRX / під столом)\n"
        
        "• 🧱 <b>Планка:</b> 2×60 сек\n"
    ),

    1: (
        "👣 <b>Вівторок: Legs Strength (Без осьового)</b>\n"
        "<i>Сила + стабілізація.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        
        "• 🚶‍♂️ <b>Випади + вага:</b> 3×10/нога\n"
        
        "• 🪑 <b>Болгарські присідання:</b> 3×8–12/нога\n"
        
        "• 🍑 <b>Ягодичний міст + вага:</b> 3×12–15\n"
        
        "• 🦿 <b>Гомілка:</b> 4×15–25\n"
    ),

    2: (
        "🧱 <b>Середа: Recovery & Mobility</b>\n"
        "<i>Розвантаження + рухливість.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        
        "• 🚴‍♂️ <b>Легка активність:</b> 5–10 хв (велосипед / ходьба)\n"
        
        "• 🧘‍♂️ <b>Розтяжка:</b> 5–10 хв (ноги + спина)\n"
    ),

    3: (
        "🦿 <b>Четвер: Upper Thickness & Control</b>\n"
        "<i>Товщина спини + контроль.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        
        "• 🧗‍♂️ <b>Підтягування (повільні):</b> 3×6–8\n"
        
        "• 🔁 <b>Горизонтальна тяга:</b> 4×10–15\n"
        
        "• 🤸‍♂️ <b>Віджимання (повільні):</b> 3×10–12\n"
        
        "• 💪 <b>Біцепс (резинка):</b> 2–3 підходи\n"
        
        "• 🧱 <b>Core (планка):</b> 2 підходи\n"
    ),

    4: (
        "🔥 <b>П'ятниця: Legs Volume (Контрольований об'єм)</b>\n"
        "<i>Без перевантаження ЦНС.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        
        "• 🚶‍♂️ <b>Випади:</b> 2×15/нога\n"
        
        "• 🦵 <b>Присідання + вага (контроль):</b> 3×12–15\n"
        
        "• 🍑 <b>Ягодичний міст:</b> 3×15\n"
        
        "• 🦿 <b>Гомілка:</b> 4×20\n"
    ),

    5: (
        "🌳 <b>Субота: Rest / Walk</b>\n"
        "<i>Відновлення.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        "• 🚶‍♂️ Прогулянка\n"
    ),

    6: (
        "🛠 <b>Неділя: Maintenance</b>\n"
        "<i>Легка активність.</i>\n\n"
        "• 🌬 <b>Вакуум:</b> 5×15-20 сек\n"
        "• 💆‍♂️ Легка активність\n"
    )
}

HYDRATION_MESSAGES = [
    "💧 Час залити охолоджуючу рідину (H2O).",
    "🥤 Суглоби самі себе не змастять. Пий воду.",
    "🚰 Перерва на гідратацію. Нирки скажуть спасибі.",
    "🌊 Рівень рідини в системі низький. Поповни баланс.",
    "🧊 Ковток води — і мозок працює краще."
]

