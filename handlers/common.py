# handlers/common.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("🤷‍♂️ Немає чого скасовувати.")
        return
    await state.clear()
    await message.answer("👌 Скасовано.")
