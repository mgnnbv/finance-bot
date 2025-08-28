from datetime import datetime
from typing import Callable, Dict, Any, Awaitable
import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import Message


class SubscriptionMiddleware:
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        async with aiosqlite.connect("Finance_for_bot.db") as db:
            async with db.execute(
                "SELECT active_subscribe, subscribe_status FROM subscribes WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                active_until, status = row
                if datetime.fromisoformat(active_until) < datetime.now():
                    await db.execute(
                        "UPDATE subscribes SET subscribe_status = 0 WHERE user_id = ?",
                        (user_id,)
                    )
                    await db.commit()
                    status = 0
            else:
                status = 0

        data["has_subscription"] = bool(status)
        return await handler(event, data)


class SubscribeCheckMiddleware(BaseMiddleware):
    def __init__(self, data_base):
        self.db = data_base

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
) -> Any:
        user_id = event.from_user.id

        async with self.db.execute('''SELECT active_subscribe FROM subscribes WHERE user_id = ?''',
                                   (user_id,)) as cursor:
            row = await cursor.fetchone()

        now = datetime.now()
        has_subscription = row and datetime.fromisoformat(row[0]) > now

        if event.text.startswith('/vip') and not has_subscription:
            await event.answer('Вам нужно обновить подписку')
            return

        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, data_base):
        self.db = data_base

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        action = event.text

        await self.db.execute('''INSERT INTO logs(user_id, action, data_of_create) VALUES (?, ?, ?)''',
                              (user_id, action, datetime.now().isoformat()))

        await self.db.commit()

        return await handler(event, data)




