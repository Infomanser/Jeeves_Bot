# services/weather_api.py
import aiohttp
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "settings.json"

# Дефолтні координати (якщо нічого не налаштовано)
DEFAULT_CONFIG = {
    "weather": {
        "name": "Chernihiv",
        "lat": 51.4982,
        "lon": 31.2893
    }
}

# --- Settings Management ---
def _load_settings() -> Dict:
    if not SETTINGS_FILE.exists():
        return DEFAULT_CONFIG
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return DEFAULT_CONFIG

def _save_settings(new_config: Dict):
    current = _load_settings()
    current.update(new_config)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)

def set_city_coords(name: str, lat: float, lon: float):
    config = {
        "weather": {
            "name": name,
            "lat": lat,
            "lon": lon
        }
    }
    _save_settings(config)

# --- Geocoding (Пошук міста) ---
async def search_city(query: str) -> Optional[Dict]:
    """Шукає місто за назвою і повертає координати першого результату."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1&language=uk&format=json"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "results" in data and data["results"]:
                        city = data["results"][0]
                        return {
                            "name": city.get("name"),
                            "lat": city.get("latitude"),
                            "lon": city.get("longitude"),
                            "country": city.get("country", "")
                        }
        except: pass
    return None

# --- Weather Forecast (Оновлена) ---
# Коди погоди WMO
WMO_CODES = {
    0: "☀️ Ясно", 1: "🌤 Переважно ясно", 2: "⛅️ Мінлива хмарність", 3: "☁️ Похмуро",
    45: "🌫 Туман", 48: "🌫 Туман з інеєм",
    51: "🌦 Легка мряка", 53: "🌦 Мряка", 55: "🌧 Щільна мряка",
    61: "🌧 Слабкий дощ", 63: "🌧 Дощ", 65: "🌧 Сильний дощ",
    71: "❄️ Слабкий сніг", 73: "❄️ Сніг", 75: "❄️ Сильний сніг",
    77: "❄️ Снігові зерна",
    80: "🌦 Зливи", 81: "🌧 Сильні зливи", 82: "⛈ Дуже сильні зливи",
    95: "⛈ Гроза", 96: "⛈ Гроза з градом", 99: "⛈ Сильна гроза з градом"
}

async def get_weather_forecast(*args, **kwargs) -> str:
    settings = _load_settings().get("weather", DEFAULT_CONFIG["weather"])
    lat, lon, city_name = settings["lat"], settings["lon"], settings["name"]

    url = (f"https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
           f"apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=kmh")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200: 
                    logging.error(f"Weather API error: {resp.status}")
                    return "❌ Сервіс погоди тимчасово недоступний."
                data = await resp.json()
                
        cur = data.get('current', {})
        if not cur:
            return "❌ Не вдалося отримати поточні дані погоди."

        code = cur.get('weather_code', 0)
        desc = WMO_CODES.get(code, f"Невідомо ({code})")
        
        logging.info(f"Weather updated for {city_name}: {cur.get('temperature_2m')}°C")

        return (
            f"🌤 <b>Погода ({city_name}):</b>\n"
            f"🌡 <b>Температура:</b> {cur.get('temperature_2m', '??')}°C (відчувається {cur.get('apparent_temperature', '??')}°C)\n"
            f"☁️ <b>Небо:</b> {desc}\n"
            f"💨 <b>Вітер:</b> {cur.get('wind_speed_10m', '??')} км/год\n"
            f"💧 <b>Вологість:</b> {cur.get('relative_humidity_2m', '??')}%"
        )
    except Exception as e:
        return f"❌ Помилка: {e}"
