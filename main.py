import asyncio

import logging

import aiosqlite
from environs import Env

from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher, types

from data_bases.finance_bd import init_db
from handlers.handlers import router

from middlewarres.middlewarre import SubscribeCheckMiddleware, LoggingMiddleware


env = Env()
env.read_env()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=env('TOKEN'), default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
dp.include_router(router=router)


async def main():
    await init_db()

    db = await aiosqlite.connect('Finance_for_bot.db')
    dp.message.middleware(SubscribeCheckMiddleware(db))
    dp.message.middleware(LoggingMiddleware(db))

    await bot.delete_webhook(drop_pending_updates=True)

    await bot.set_my_commands([
        types.BotCommand(command='/add_expense', description='Добавление расходов'),
        types.BotCommand(command='/report', description='Генерация отчета'),
        types.BotCommand(command='/categories', description='Просмотр всех категорий и добавление новой'),
    ])

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
