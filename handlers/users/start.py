from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart

from loader import dp

from utils.db_api.sql import DBCommands
database = DBCommands()


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    user_in_db = database.access()
    if user_in_db:
        text = [
            f'Здравствуйте, {message.from_user.full_name}!',
            'Для получения справки по коммандам введите комманду /help'
        ]
    else:
        text = [
            f'Здравствуйте, {message.from_user.full_name}!',
            'Для получения полного функционала вам необходимо авторизоваться /oauth',
        ]
    await message.answer('\n'.join(text))