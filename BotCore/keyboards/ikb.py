from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import KeyboardBuilder

from General import config as cfg

start_menu = InlineKeyboardMarkup(
	inline_keyboard=[
		[InlineKeyboardButton(text="Товары", web_app=WebAppInfo(url=cfg.WEB_URL + "/giveaway"))],
		[
			InlineKeyboardButton(text="Поддержка", url="https://t.me/breitenbuecher"),
			InlineKeyboardButton(text="Профиль", callback_data="profile")
		]
	]
)

back_to_start = InlineKeyboardMarkup(
	inline_keyboard=[
		[InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
	]
)


def profile_kb(is_admin: bool):
	kb = KeyboardBuilder(types.InlineKeyboardButton)

	if is_admin:
		kb.row(InlineKeyboardButton(text="Создать розыгрыш", callback_data="create_ruffle_prizes"))

	kb.row(InlineKeyboardButton(text="Пополнить баланс", callback_data="balance_top_up"))
	kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_start"))
	return kb.as_markup()

