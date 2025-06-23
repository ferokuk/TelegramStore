from ..keyboards.catalog_kb import main_menu_kb
from aiogram import Router, types, F

router = Router()


@router.message(F.text == '/start')
async def cmd_start(message: types.Message):
    text = f'Добро пожаловать, {message.from_user.first_name or message.from_user.username}! Выберите раздел:'
    await message.answer(text, reply_markup=main_menu_kb())
