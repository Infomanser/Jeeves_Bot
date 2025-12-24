# utils/helpers.py
from datetime import datetime

def get_time_greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 12: return "🌅 Доброго ранку"
    if 12 <= h < 18: return "☀️ Добрий день"
    if 18 <= h < 23: return "🍸 Доброго вечора"
    return "🌙 Доброї ночі"
