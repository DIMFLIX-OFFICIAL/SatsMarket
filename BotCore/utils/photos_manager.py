import base64
from io import BytesIO

import aiofiles
from PIL import Image
from aiogram import Bot
from aiogram.types import BufferedInputFile
from async_lru import alru_cache


class Photo:
    @classmethod
    @alru_cache
    async def file(cls, filename: str = "main.png") -> BufferedInputFile:
        async with aiofiles.open("General/assets/" + filename, 'rb') as f:
            photo = await f.read()

        return BufferedInputFile(photo, filename)

    @classmethod
    async def avatar(cls, bot: Bot, user_id: int) -> BufferedInputFile:
        user_chat = await bot.get_chat(user_id)

        if user_chat.photo is not None:
            user_photo_id = await bot.get_file(user_chat.photo.big_file_id)
            user_photo = await bot.download_file(user_photo_id.file_path)
            return BufferedInputFile(user_photo.read(), "LunarLegacy.png")

        return await cls.file()

    @classmethod
    def compress_img(cls, photo_bytes, *, quality, width, height, format="JPEG") -> str:
        photo_bytes_io = BytesIO(photo_bytes)
        img = Image.open(photo_bytes_io)
        img.thumbnail((width, height))

        buffered = BytesIO()
        img.save(buffered, format=format, optimize=True, quality=quality)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

