import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import aiohttp

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "jeeves.db"

DEFAULT_CONFIG = {
    "name": "Chernihiv",
    "lat": 51.4982,
    "lon": 31.2893
}

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

def get_user_city(user_id: int) -> dict:
    """Отримує координати користувача з БД. Якщо немає — дефолт."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT city_name, lat, lon FROM user_weather WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            
            if row:
                return {"name": row[0], "lat": row[1], "lon": row[2]}
    except Exception as e:
        logging.error(f"Database error in get_user_city: {e}")
            
    return DEFAULT_CONFIG

def set_city_coords(user_id: int, name: str, lat: float, lon: float):
    """Зберігає або оновлює координати для конкретного користувача."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_weather (user_id, city_name, lat, lon)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                city_name=excluded.city_name,
                lat=excluded.lat,
                lon=excluded.lon
        """, (user_id, name, lat, lon))
        conn.commit()

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

async def get_weather_forecast(user_id: int, *args, **kwargs) -> str:
    settings = get_user_city(user_id)
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

async def get_weekly_forecast(user_id: int) -> str:
    settings = get_user_city(user_id)
    lat, lon, city_name = settings["lat"], settings["lon"], settings["name"]
    
    url = (f"https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min"
           f"&timezone=auto")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200: return "❌ Прогноз на тиждень недоступний."
            data = await resp.json()
    
    daily = data.get("daily", {})
    days = daily.get("time", [])
    codes = daily.get("weather_code", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])

    res = [f"🗓 <b>Прогноз на тиждень ({city_name}):</b>"]
    
    days_ua = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    
    for i in range(len(days)):
        dt = datetime.strptime(days[i], "%Y-%m-%d")
        day_name = days_ua[dt.weekday()]
        icon = WMO_CODES.get(codes[i], "❓").split()[0]
        
        line = f"<code>{day_name} {dt.strftime('%d.%m')}</code> {icon} <b>{t_min[i]}°..{t_max[i]}°</b>"
        res.append(line)
        
    return "\n".join(res)
    