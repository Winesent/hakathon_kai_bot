import asyncio
import logging
import json
import os

from dotenv import load_dotenv


from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import sqlite3

load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = Bot(TOKEN)

connection = sqlite3.connect('users.db')
cursor = connection.cursor()
router = Router()
start_text = '''Привет, {full_name}. Я - бот. Напишите своё ФИО.'''
keyboard = ReplyKeyboardMarkup(keyboard=
                               [[KeyboardButton(text='Задать вопрос')], [KeyboardButton(text='Админ-панель')]],
                               resize_keyboard=True)
keyboard_back = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отмена')]], resize_keyboard=True)
keyboard_admin = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Посмотреть БД')],
                                               [KeyboardButton(text='Изменить баллы')]],
                                     resize_keyboard=True)


class AwaitMessages(StatesGroup):
    fio = State()
    group_number = State()


class StudentQuestion(StatesGroup):
    question = State()


class AdminUser(StatesGroup):
    user_login = State()
    action = State()


@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    search = cursor.execute('SELECT * from users WHERE uid == ?', (user_id,)).fetchone()
    if not search:
        await message.answer('Для работы с ботом требуется зарегистрироваться! Использовать бот '
                             'имеют право только студенты КАИ!')
        await state.set_state(AwaitMessages.fio)
        await message.answer('Введите своё ФИО через пробел. Например: Иванов Иван Иванович')
    else:
        await message.answer('Вы можете задать вопрос, на который ответят студенты КАИ!', reply_markup=keyboard)


@router.message(AwaitMessages.fio)
async def process_fio(message: Message, state: FSMContext) -> None:
    await state.update_data(fio=message.text)
    await state.set_state(AwaitMessages.group_number)
    await message.answer(f'Приятно познакомиться, {message.text}! Теперь напишите свой номер группы. Например: 6110')


@router.message(AwaitMessages.group_number)
async def process_group_number(message: Message, state: FSMContext) -> None:
    await state.update_data(group_number=message.text)
    data = await state.get_data()
    cursor.execute('INSERT INTO users (uid, fio, group_number, points, login, admin) VALUES (?, ?, ?, ?, ?, ?)',
                   (message.from_user.id, data['fio'], data['group_number'], 0,
                    message.from_user.username, 0),)
    connection.commit()
    await message.answer('Поздравляю, вы зарегистрированы в системе! Перейдите по ссылке-приглашению:'
                         '\nhttps://t.me/+7b969FJ0z6E2N2My', reply_markup=keyboard)
    await state.clear()


@router.message(StudentQuestion.question)
async def set_question(message: Message, state: FSMContext) -> None:
    await state.update_data(question=message.text)
    if message.text == 'Отмена':
        await message.answer('Процесс задавания вопроса отменен.', reply_markup=keyboard)
        await state.clear()
        return
    data = await state.get_data()
    await message.answer('Вопрос отправляется.')
    await bot.send_message(chat_id=-1002346373266, text=f'{message.text}')
    await message.answer('Вопрос успешно отправлен', reply_markup=keyboard)
    await state.clear()


@router.message(F.text == 'Задать вопрос')
async def check(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    search = cursor.execute('SELECT * from users WHERE uid == ?', (user_id,)).fetchone()
    if not search:
        await message.answer('Вы не зарегистрированы в системе. Используйте команду: /start')
    if search:
        if message.text == 'Задать вопрос':
            await state.set_state(StudentQuestion.question)
            await message.answer('Задавайте свой вопрос в свободной форме!', reply_markup=keyboard_back)


@router.message(F.text == 'Админ-панель')
async def admin_panel(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    search = cursor.execute('SELECT admin FROM users WHERE uid == ?', (user_id,)).fetchone()
    if search[0]:
        await message.answer('Добро пожаловать, администратор! Используйте клавиатуру для работы с панелью.',
                             reply_markup=keyboard_admin)
    else:
        await message.answer('Вы не являетесь администратором! Доступ воспрещен.', reply_markup=keyboard)


@router.message(F.text == 'Посмотреть БД')
async def admin_panel(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    search = cursor.execute('SELECT admin FROM users WHERE uid == ?', (user_id,)).fetchone()
    if search[0]:
        bd = cursor.execute('SELECT * from users').fetchall()
        base = 'ID | USER ID | FIO | GROUP NUMBER | POINTS | LOGIN | ADMIN\n'
        for user in bd:
            user = list(map(str, user))
            base += f'{" | ".join(user)}\n'
        await message.answer(f'{base}', reply_markup=keyboard_admin)
    else:
        await message.answer('Вы не являетесь администратором! Доступ воспрещен.', reply_markup=keyboard)


@router.message(AdminUser.user_login)
async def edit_user(message: Message, state: FSMContext) -> None:
    login = message.text
    search = cursor.execute('SELECT * FROM users WHERE login == ?', (login, )).fetchone()
    base = ('ИНФОРМАЦИЯ ОБ УЧАСТНИКЕ:\n'
            'ID | USER ID | FIO | GROUP NUMBER | POINTS | LOGIN | ADMIN\n')
    if search:
        await state.update_data(user_login=message.text)
        base += f'{" | ".join(list(map(str, search)))}'
        await message.answer(f'{base}')
        await message.answer('Укажите только число, если хотите УСТАНОВИТЬ определенное значение баллов.\n'
                             'Если вы хотите прибавить или отнять количество баллов, то используйте'
                             'математический знак перед числом.\n'
                             'Например:\n'
                             'Для снятия баллов напишите: *-15* (Отнимет у участника 15 баллов\n'
                             'Для прибавления баллов напишите: *+15* (Прибавит участнику 15 баллов')
        await state.set_state(AdminUser.action)
    else:
        await message.answer('Такого пользователя не существует.', reply_markup=keyboard_admin)
        await state.clear()


@router.message(AdminUser.action)
async def action(message: Message, state: FSMContext) -> None:
    await state.update_data(action=message.text)
    data = await state.get_data()
    act = data['action']
    if '+' in act or '-' in act:
        act = int(act)
        points = cursor.execute('SELECT points FROM users WHERE login = ?', (data['user_login'],)).fetchone()
        points = int(points[0]) + act
        cursor.execute('UPDATE users SET points = ? WHERE login = ?', (points, data['user_login']))
        connection.commit()
        await state.clear()
        await message.answer('Обновление баллов успешно прошло.', reply_markup=keyboard_admin)
    else:
        act = int(act)
        cursor.execute('UPDATE users SET points = ? WHERE login = ?', (act, data['user_login']))
        connection.commit()
        await state.clear()
        await message.answer('Обновление баллов успешно прошло.', reply_markup=keyboard_admin)


@router.message(F.text == 'Изменить баллы')
async def admin_panel(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    search = cursor.execute('SELECT admin FROM users WHERE uid == ?', (user_id,)).fetchone()
    if search[0]:
        await message.answer('Напишите логин требуемого вам участника.')
        await state.set_state(AdminUser.user_login)
    else:
        await message.answer('Вы не являетесь администратором! Доступ воспрещен.', reply_markup=keyboard)


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
