from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp
from utils.misc import rate_limit

from utils.db_api.sql import DBCommands
database = DBCommands()


@rate_limit(5, 'help')
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    user_in_db = database.access()
    if user_in_db:
        text = [
            'Список команд: ',
            '/cards - Работа с карточками',
            '/help - Получить справку'
        ]
    else:
        text = [
            'Для получения полного функционала вам необходимо авторизоваться /oauth',
        ]
    await message.answer('\n'.join(text))