from aiogram.fsm.state import State, StatesGroup


class AddExpense(StatesGroup):
    chose_amount = State()
    chose_category = State()
    chose_description = State()


class AddCategory(StatesGroup):
    chose_name = State()
