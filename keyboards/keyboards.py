from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3


def category_keyboard(row_amount=3):
    with sqlite3.connect('Finance_for_bot.db') as db:
        cursor = db.cursor()
        cursor.execute("SELECT name FROM category")
        rows = cursor.fetchall()

    if not rows:
        return None

    inline_keyboard = []
    buttons = [InlineKeyboardButton(text=row[0], switch_inline_query_current_chat=row[0]) for row in rows]

    for i in range(0, len(buttons), row_amount):
        inline_keyboard.append(buttons[i:i + row_amount])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def subscribe_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[
                                        [
                                            KeyboardButton(text='/subscribe'),
                                            KeyboardButton(text='/data_of_subscribe')]
                                        ])
    return keyboard


