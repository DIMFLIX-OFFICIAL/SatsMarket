from aiogram import types
from General.loader import bot, dp

@dp.message()
async def other_way(message: types.Message) -> None:
	await bot.delete_message(message.from_user.id, message.message_id)
