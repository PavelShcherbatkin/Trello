from authlib.integrations.requests_client import OAuth1Session
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

oauth = None
oauth_id = None
boards = None
boards_list = None

name_board = None
board_id = None
lists = None
lists_list = None

name_list = None
list_id = None

task = None

date = None

members = None
memberships_name_list = None

name_member = None
member_id = None



# Получение списка досок
@dp.message_handler(Command('cards'))
async def oauth(message: types.Message):
    global oauth
    global oauth_id
    global boards_list
    global boards
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
    boards_list = []
    for board in boards:
        boards_list.append(board['name']) 
    boards_keyboard = types.InlineKeyboardMarkup()
    for name in boards_list:
        bt_board = types.InlineKeyboardButton(name, callback_data=name)
        boards_keyboard.add(bt_board)
    await message.answer("Выберите доску:", reply_markup=boards_keyboard)


# Получение списка списков (тыкнули на какую-то доску)
@dp.callback_query_handler(lambda c: c.data in boards_list)
async def process_callback(call: types.CallbackQuery):
    global name_board
    global board_id
    global lists
    global lists_list
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
    url_lists = f'https://api.trello.com/1/boards/{board_id}/lists'
    lists = oauth.get(url_lists).json()
    lists_list = []
    for l in lists:
        lists_list.append(l['name'])
    lists_keyboard = types.InlineKeyboardMarkup()
    for name in lists_list:
        bt_list = types.InlineKeyboardButton(name, callback_data=name)
        lists_keyboard.add(bt_list)
    await dp.bot.send_message(call.from_user.id, "Выберите список:", reply_markup=lists_keyboard)


# Получение action (тыкнули на какой-то список)
@dp.callback_query_handler(lambda c: c.data in lists_list)
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
    
    kb_action_1 = InlineKeyboardButton('Посмотреть текущие задачи', callback_data='read')
    kb_action_2 = InlineKeyboardButton('Загрузить новую задачу', callback_data='write')
    action_keyboard = InlineKeyboardMarkup()
    action_keyboard.add(kb_action_1)
    action_keyboard.add(kb_action_2)

    await dp.bot.send_message(call.from_user.id, "Что вы хотите сделать?", reply_markup=action_keyboard)


# (тыкнули на read)
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
    text = f'{text_cards[0]}\n' + ';\n'.join(text_cards[1:]) + '.'
    await dp.bot.send_message(call.from_user.id, text)


# (тыкнули на read)
@dp.callback_query_handler(lambda c: c.data == 'write')
async def process_callback(call: types.CallbackQuery):
    await dp.bot.answer_callback_query(call.id)
    await dp.bot.send_message(call.from_user.id, 'Введите имя задачи')
    await Date.D1.set()


# Ввели имя задачи
@dp.message_handler(state=Date.D1)
async def process_callback(message: types.Message, state: FSMContext):
    global task
    task = message.text
    await state.finish()
    kb_date_yes = InlineKeyboardButton('Установить дату', callback_data='date_yes')
    kb_date_no = InlineKeyboardButton('Не ставить дату', callback_data='date_no')
    date_keyboard = InlineKeyboardMarkup()
    date_keyboard.add(kb_date_yes)
    date_keyboard.add(kb_date_no)
    await message.answer("Хотите установить дату?", reply_markup=date_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'date_no')
async def process_callback(call: types.CallbackQuery):
    global date
    await dp.bot.answer_callback_query(call.id)
    date = None
    await Date.D2.set()
    bt = KeyboardButton('Подтвердить')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(bt)
    await dp.bot.send_message(call.from_user.id, 'Подтвердите данное действие', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'date_yes')
async def process_callback(call: types.CallbackQuery):
    await dp.bot.send_message(call.from_user.id, "Пожалуйста, выберите дату: ", reply_markup=create_calendar())


@dp.callback_query_handler(calendar_callback.filter()) 
async def process_name(call: CallbackQuery, callback_data: dict):
    global date
    selected, date = await process_calendar_selection(call, callback_data)
    if selected:
        await dp.bot.answer_callback_query(call.id)
        await dp.bot.send_message(call.from_user.id, 'Введите время в формате hour:minut:second')
        await Date.D2.set()


@dp.message_handler(state=Date.D2)
async def add_task(message: types.Message, state: FSMContext):
    global date
    time = message.text
    if time != 'Подтвердить':
        date = date.strftime("%Y-%m-%d") + ' ' + time
    else:
        pass
    await state.finish()

    kb_members_yes = InlineKeyboardButton('Назначить исполнителя', callback_data='members')
    kb_members_no = InlineKeyboardButton('Не назначать исполнителя', callback_data='no_members')
    members_keyboard_lists = InlineKeyboardMarkup()
    members_keyboard_lists.add(kb_members_yes)
    members_keyboard_lists.add(kb_members_no)

    await message.answer("Хотите назначить исполнителя?", reply_markup=members_keyboard_lists)


@dp.callback_query_handler(lambda c: c.data == 'no_members')
async def process_callback(call: types.CallbackQuery):
    await dp.bot.answer_callback_query(call.id)
    await Date.D3.set()
    bt_member_confirm = KeyboardButton('Подтвердить')
    keyboard_confirm = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard_confirm.add(bt_member_confirm)
    await dp.bot.send_message(call.from_user.id, 'Подтвердите данное действие', reply_markup=keyboard_confirm)
    await Date.D3.set()


@dp.callback_query_handler(lambda c: c.data == 'members')
async def process_callback(call: types.CallbackQuery):
    global members
    global memberships_name_list
    await dp.bot.answer_callback_query(call.id)
    members_url = f'https://api.trello.com/1/boards/{board_id}/members'
    members = oauth.get(members_url).json()
    memberships_name_list = []
    for membership in members:
        memberships_name_list.append(membership['fullName']) 
    memberships_keyboard = types.InlineKeyboardMarkup()
    for name in memberships_name_list:
        bt_member = InlineKeyboardButton(name, callback_data=name)
        memberships_keyboard.add(bt_member)
    await dp.bot.send_message(call.from_user.id, 'Выберите исполнителя', reply_markup=memberships_keyboard)


@dp.callback_query_handler(lambda c: c.data in memberships_name_list)
async def process_callback(call: types.CallbackQuery):
    global name_member
    global member_id
    await dp.bot.answer_callback_query(call.id)
    name_member = call.data
    members_id = []
    for member in members:
        ans = {i: member[i] for i in member if member['fullName'] == name_member}
        try:
            members_id.append(ans['id'])
        except:
            pass
    member_id = members_id[0]

    bt_member_yes_confirm = KeyboardButton('Да')
    keyboard_yes_confirm = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard_yes_confirm.add(bt_member_yes_confirm)
    await dp.bot.send_message(call.from_user.id, 'Подтвердите данное действие', reply_markup=keyboard_yes_confirm)
    await Date.D3.set()


@dp.message_handler(state=Date.D3)
async def add_task(message: types.Message, state: FSMContext):
    global list_id
    global task
    global date
    global member_id

    url_cards = f'https://api.trello.com/1/cards'
    confirm = message.text
    if confirm != 'Подтвердить':
        query = {
                'idList': list_id,
                'name': task,
                'due': date,
                'idMembers': member_id
            }
    else:
        query = {
                'idList': list_id,
                'name': task,
                'due': date
            }   
    cards = oauth.post(url_cards, data=query)
    await message.answer(f'Карточка "{task}" добавлена')
    task = None
    date = None
    member_id = None
    await state.finish()
