from datetime import datetime, timedelta

import aiosqlite
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from data_bases.finance_bd import category_check, add_expense, report

from fsm.fsm import AddExpense, AddCategory, VipReport

from keyboards.keyboards import category_keyboard, subscribe_keyboard

router = Router()

BLOCKED = {'/categories', '/report', '/add_expense', '/start'}


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer('Здраствуйте это бот для контроля ваших расходов и других финансовых операций',
                         reply_markup=subscribe_keyboard())


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
        async with aiosqlite.connect("Finance_for_bot.db") as db:
            await db.execute(
                '''INSERT INTO category (name)
                   VALUES (?)''', (data['name'],))

            await db.commit()

        await message.answer('Поздравляю категория была добавлена!!')
        await state.clear()


@router.message(StateFilter(None), Command('add_expense'))
async def add_expense_cmd(message: Message, state: FSMContext):
    async with aiosqlite.connect('Finance_for_bot.db') as db:
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


@router.message(Command('vip_report'))
async def vip_report_cmd(message: Message, has_subscription: bool, state: FSMContext):
    if has_subscription:
        await message.answer('Напишите категорию трат, которые вы хотите увидеть',
                             reply_markup=category_keyboard())
        await state.set_state(VipReport.category_name)
    else:
        await message.answer('У вас нет подписки')


@router.message(VipReport.category_name)
async def category_report(message: Message, state: FSMContext):
    data = message.text.lower()[9:]
    await state.clear()
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        async with db.execute(
                'SELECT amount, description, data_of_operation FROM finance WHERE category_name = ?',
                (data,)
        ) as cursor:
            rows = await cursor.fetchall()

            if rows:

                for row in rows:
                    await message.answer(
                        f'Все траты в категории: {data}\n'
                        f'Сумма: {row[0]}р\n'
                        f'Описание: {row[1]}\n'
                        f'Дата совершения траты: {row[2]}'
                    )

            else:
                await message.answer('У вас нет такой категории')


@router.message(Command('report'))
async def report_cmd(message: Message):
    result = await report()

    if not result:
        await message.answer('Операций нет')
    else:
        for row in result:
            id_, date, amount, description = row
            await message.answer(f"Операция №: {id_}\nДата: {date}\nСумма: {amount}р\nОписание: {description}")


@router.message(Command('subscribe'))
async def subscribe_cmd(message: Message):
    user_id = message.from_user.id
    active_sub = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
    subscribe_status = 1
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        async with db.execute('SELECT user_id, subscribe_status, active_subscribe FROM subscribes WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                if row[1] == 1:
                    await message.answer(f'Ваша подписка все еще действует до: {row[2]}')
                    return
                else:
                    await message.answer('Ваша подписка закончилась, мы продлим вам ее')
                    await db.execute(
                        '''INSERT OR REPLACE INTO subscribes(user_id, active_subscribe, subscribe_status)
                           VALUES(?, ?, ?)''',
                        (user_id, active_sub, subscribe_status))
                    await message.answer('Поздравляю, ваша подписка продлена!!')
            else:
                await db.execute(
                    '''INSERT OR REPLACE INTO subscribes(user_id, active_subscribe, subscribe_status)
                       VALUES(?, ?, ?)''',
                    (user_id, active_sub, subscribe_status))

                await db.commit()

    await message.answer('Подписка оформлена, поздравляю!!!')


@router.message(Command('data_of_subscribe'))
async def data_of_subscribe(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('Finance_for_bot.db') as db:
        async with db.execute('''SELECT active_subscribe FROM subscribes WHERE user_id = ?''', (user_id,)) as cursor:
            row = await cursor.fetchone()

            if row:
                try:
                    date = datetime.fromisoformat(row[0].strip('"'))
                except ValueError:
                    date = datetime.strptime(row[0].strip('"'), "%d.%m.%Y")
                await message.answer(f'Подписку вы оформили до: {date:%d.%m.%Y %H:%M}')
            else:
                await message.answer('Подписки нет')


@router.callback_query()
async def callback_handler(callback: CallbackQuery):
    await callback.message.answer(callback.data)
    await callback.answer()
