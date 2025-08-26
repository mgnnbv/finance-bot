from datetime import datetime

import aiosqlite
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from data_bases.finance_bd import category_check, add_expense, report

from fsm.fsm import AddExpense, AddCategory

from keyboards.keyboards import category_keyboard

router = Router()

BLOCKED = {'/categories', '/report', '/add_expense', '/start'}


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer('Здраствуйте это бот для контроля ваших расходов и других финансовых операций')


@router.message(StateFilter(None), Command('add_expense'))
async def add_expense_cmd(message: Message, state: FSMContext):
    async with aiosqlite.connect('../Finance.db') as db:
        async with db.execute("SELECT name FROM category") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("Категорий нет. Сначала добавьте категорию через /add_category.")
        return
    else:
        await message.answer('Напишите сумму которую вы потратили')
        await state.set_state(AddExpense.chose_amount)


@router.message(AddExpense.chose_amount)
async def choosing_amount(message: Message, state: FSMContext):
    await state.update_data(chosen_amount=message.text)
    await message.answer('Выберите категорию\n⬇ ⬇ ⬇ ⬇ ⬇',
                         reply_markup=category_keyboard())
    await state.set_state(AddExpense.chose_category)


@router.message(AddExpense.chose_category)
async def choosing_category(message: Message, state: FSMContext):
    await state.update_data(chosen_category=message.text[9:])
    await message.answer('И опишите вашу трату')
    await state.set_state(AddExpense.chose_description)


@router.message(AddExpense.chose_description)
async def choosing_description(message: Message, state: FSMContext):
    await state.update_data(chosen_description=message.text)
    result = await state.get_data()

    result["user_id"] = message.from_user.id
    result["data_of_operation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await message.answer('Поздравляю мы сохранили вашу трату в базу')
    await state.clear()
    await add_expense(result)


@router.message(Command('report'))
async def report_cmd(message: Message):
    result = await report()

    if not result:
        await message.answer('Операций нет')
    else:
        for row in result:
            await message.answer(row)


@router.message(StateFilter(None), Command('categories'))
async def categories_cmd(message: Message, state: FSMContext):
    result = await category_check()

    if not result:
        await message.answer('Категорий нет')
    else:
        for row in result:
            await message.answer(row)

    await message.answer('А теперь введите категорию которую хотите добавить')
    await state.set_state(AddCategory.chose_name)


@router.message(AddCategory.chose_name)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(name=message.text.lower())
    data = await state.get_data()
    if data['name'] in BLOCKED:
        await message.answer('Нельзя добавить такую категорию')
        await state.clear()
        return
    else:
        async with aiosqlite.connect("Finance.db") as db:
            await db.execute(
                '''INSERT INTO category (name)
                   VALUES (?)''', (data['name'],))

            await db.commit()

        await message.answer('Поздравляю категория была добавлена!!')
        await state.clear()


@router.callback_query()
async def callback_handler(callback: CallbackQuery):
    await callback.message.answer(callback.data)
    await callback.answer()
