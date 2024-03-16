import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, types

from General.loader import db


class AddUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event.message, types.Message):
            user_id = event.message.from_user.id
            username = event.message.from_user.username
        elif isinstance(event.callback_query, types.CallbackQuery):
            user_id = event.callback_query.from_user.id
            username = event.callback_query.from_user.username
        elif isinstance(event.inline_query, types.InlineQuery):
            user_id = event.inline_query.from_user.id
            username = event.inline_query.from_user.username
        else:
            return

        if await db.get_user(user_id) is None:
            await db.add_user(user_id, username)
        else:
            await db.update_user_online(user_id, latest_online=datetime.datetime.now())

        return await handler(event, data)
