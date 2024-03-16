from aiogram import types
from aiogram.filters import Filter

from General import config as cfg


class MyFilter(Filter):
    def __init__(self) -> None: ...

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == cfg.ADMIN_ID

