from authlib.integrations.requests_client import OAuth1Session
import socket
from aiogram import types

from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext

from loader import dp

from utils.db_api.sql import DBCommands
database = DBCommands()

from states.date import Date
from data.config import trello_key, trello_secret

# Кнопки
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogramcalendar.aiogramcalendar import calendar_callback, create_calendar, process_calendar_selection


client_key = trello_key
client_secret = trello_secret

oauth_id = None
name_board = None
board_id = None
name_list = None
list_id = None
date = None
task = None

@dp.message_handler(Command('cards'))
async def oauth(message: types.Message):
    global oauth_id
    oauth_token, oauth_token_secret = await database.access()
    oauth = OAuth1Session(
        client_key,
        client_secret,
        token = oauth_token,
        token_secret = oauth_token_secret
        )
    url = 'https://api.trello.com/1/members/me'
    oauth_id = oauth.get(url).json()['id']
    url_board = f'https://api.trello.com/1/members/{oauth_id}/boards'
    boards = oauth.get(url_board).json()
    check = []
    for board in boards:
        check.append(board['name']) 
    cards_keyboard = types.InlineKeyboardMarkup()
    for name in check:
        inline_btns = types.InlineKeyboardButton(name, callback_data=name)
        cards_keyboard.add(inline_btns)

    # Обработка кнопки
    @dp.callback_query_handler(lambda c: c.data in check)
    async def process_callback(call: types.CallbackQuery):
        global name_board
        global board_id
        await dp.bot.answer_callback_query(call.id)
        name_board = call.data
        boards_id = []
        for board in boards:
            ans = {i: board[i] for i in board if board['name'] == name_board}
            try:
                boards_id.append(ans['id'])
            except:
                pass
        board_id = boards_id[0]
        url_list = f'https://api.trello.com/1/boards/{board_id}/lists'
        lists = oauth.get(url_list).json()
        check_lists = []
        for l in lists:
            check_lists.append(l['name'])
        cards_keyboard_lists = types.InlineKeyboardMarkup()
        for name in check_lists:
            inline_btns_lists = types.InlineKeyboardButton(name, callback_data=name)
            cards_keyboard_lists.add(inline_btns_lists)
    
        @dp.callback_query_handler(lambda c: c.data in check_lists)
        async def process_callback(call: types.CallbackQuery):
            global name_list
            global list_id
            await dp.bot.answer_callback_query(call.id)
            name_list = call.data
            
            list_id = []
            for l in lists:
                if l['name'] == name_list:
                    list_id.append(l['id'])
            list_id = list_id[0]
            
            kb1 = InlineKeyboardButton('Посмотреть текущие задачи', callback_data='read')
            kb2 = InlineKeyboardButton('Загрузить новую задачу', callback_data='write')
            final_keyboard_lists = InlineKeyboardMarkup()
            final_keyboard_lists.add(kb1)
            final_keyboard_lists.add(kb2)

            await message.answer("Что вы хотите сделать?", reply_markup=final_keyboard_lists)


            @dp.callback_query_handler(lambda c: c.data == 'read')
            async def process_callback(call: types.CallbackQuery):
                await dp.bot.answer_callback_query(call.id)
                url_cards = f'https://api.trello.com/1/lists/{list_id}/cards'
                cards = oauth.get(url_cards).json()
                text_cards = [
                    f'Ваши карточки на доске "{name_board}" в списке "{name_list}":',
                    ]
                for card in cards:
                    text_cards.append(card['name'])
                await message.answer('\n'.join(text_cards))

            @dp.callback_query_handler(lambda c: c.data == 'write')
            async def process_callback(call: types.CallbackQuery):
                await dp.bot.answer_callback_query(call.id)
                await message.answer('Введите имя задачи')
                await Date.D1.set()
            
            @dp.message_handler(state=Date.D1)
            async def process_callback(message: types.Message, state: FSMContext):
                global task
                task = message.text
                kb_date_yes = InlineKeyboardButton('Установить дату', callback_data='date_yes')
                kb_date_no = InlineKeyboardButton('Не ставить дату', callback_data='date_no')
                date_keyboard = InlineKeyboardMarkup()
                date_keyboard.add(kb_date_yes)
                date_keyboard.add(kb_date_no)
                await message.answer("Хотите установить дату:", reply_markup=date_keyboard)
                await state.finish()

                @dp.callback_query_handler(lambda c: c.data == 'date_no')
                async def process_callback(call: types.CallbackQuery):
                    await dp.bot.answer_callback_query(call.id)
                    button_yes = KeyboardButton('Да')
                    button_no = KeyboardButton('Нет')
                    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    greet_kb.add(button_yes)
                    greet_kb.add(button_no)

                    await message.answer(f'Хотите добавить карточку "{task}"?', reply_markup=greet_kb)
                    await Date.D3.set()
                
                @dp.callback_query_handler(lambda c: c.data == 'date_yes')
                async def process_callback(call: types.CallbackQuery):
                    await message.answer("Please select a date: ", reply_markup=create_calendar())

                    @dp.callback_query_handler(calendar_callback.filter()) 
                    async def process_name(callback_query: CallbackQuery, callback_data: dict):
                        global date
                        selected, date = await process_calendar_selection(callback_query, callback_data)
                        if selected:
                            await dp.bot.answer_callback_query(callback_query.id)
                            await message.answer('Введите время в формате hour:minut:second')
                            await Date.D2.set()
                            
                            @dp.message_handler(state=Date.D2)
                            async def add_task(message: types.Message, state: FSMContext):
                                global time
                                time = message.text
                                button_yes = KeyboardButton('Да')
                                button_no = KeyboardButton('Нет')
                                greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                                greet_kb.add(button_yes)
                                greet_kb.add(button_no)

                                await message.answer(f'Хотите добавить карточку "{task}"?', reply_markup=greet_kb)
                                await Date.D3.set()

                @dp.message_handler(state=Date.D3)
                async def add_task(message: types.Message, state: FSMContext):
                    if message.text == "Да":
                        url_cards = f'https://api.trello.com/1/cards'
                        if date:
                            query = {
                                'idList': list_id,
                                'name': task,
                                'due': date.strftime("%Y-%m-%d") + ' ' + time
                            }
                        else:
                            query = {
                                'idList': list_id,
                                'name': task,
                            }
                        cards = oauth.post(url_cards, data=query)
                    
                        await message.answer(f'Карточка "{task}" добавлена')
                        await state.finish()
                    else:
                        await message.answer(f'Хорошо, карточка "{task}" не будет добавлена')
                        await state.finish() 

        await message.answer("Выберите список:", reply_markup=cards_keyboard_lists)

    await message.answer("Выберите доску:", reply_markup=cards_keyboard)
