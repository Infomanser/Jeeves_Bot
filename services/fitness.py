# services/fitness.py
import random
from datetime import datetime
from config import FITNESS_PLAN, HYDRATION_MESSAGES

async def get_today_workout() -> str:
    weekday = datetime.now().weekday()

    plan = FITNESS_PLAN.get(weekday, "🤷‍♂️ План не знайдено. Відпочивай.")

    return plan

async def get_hydration_reminder() -> str:
    return random.choice(HYDRATION_MESSAGES) if HYDRATION_MESSAGES else "💧 Пий воду!"