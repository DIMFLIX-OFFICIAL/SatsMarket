from aiogram import types

from BotCore.utils.photos_manager import Photo
from General.loader import bot, dp, db
from General import config as cfg
from BotCore.keyboards import ikb
from BotCore.filters.callback_filters import CData


@dp.callback_query(CData("profile"))
async def start_handler(callback: types.CallbackQuery) -> None:
	balance = (await db.get_user(callback.from_user.id))["balance"]
	user_chat = await bot.get_chat(callback.from_user.id)
	text = f"Ваш ID: {callback.from_user.id}\nВаше имя: {callback.from_user.full_name}\nВаш баланс: {balance}"
	kb = ikb.profile_kb(callback.from_user.id == cfg.ADMIN_ID)

	if user_chat.photo is None:
		await bot.edit_message_caption(
			chat_id=callback.from_user.id,
			message_id=callback.message.message_id,
			caption=text,
			reply_markup=kb
		)
	else:
		await bot.send_photo(
			chat_id=callback.from_user.id,
			photo=await Photo.avatar(bot, callback.from_user.id),
			caption=text,
			reply_markup=kb
		)
		await bot.delete_message(callback.from_user.id, callback.message.message_id)
