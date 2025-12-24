# utils/filters.py
from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import OWNER_ID, ADMIN_IDS

class IsOwner(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == OWNER_ID

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS
