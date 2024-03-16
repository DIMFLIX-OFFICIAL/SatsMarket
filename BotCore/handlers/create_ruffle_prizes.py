import asyncio
import base64
from typing import Union, List
from PIL import Image
from io import BytesIO

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, PhotoSize
from aiogram_media_group import media_group_handler

from BotCore.utils.photos_manager import Photo
from General.loader import bot, dp, db
from BotCore.keyboards import ikb
from BotCore.filters.callback_filters import CData


class AddRufflePrizes(StatesGroup):
	title = State()
	description = State()
	money_needed = State()
	countdown_hours = State()
	photos = State()
	menu_icon = State()
	confirm = State()


@dp.callback_query(CData("create_ruffle_prizes"))
async def start_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
	bot_message = await bot.edit_message_caption(
		chat_id=callback.from_user.id,
		message_id=callback.message.message_id,
		caption="Окей, приступим!\nВведите название розыгрыша",
		reply_markup=ikb.back_to_start
	)

	await state.set_state(AddRufflePrizes.title)
	await state.update_data(last_bot_msg_id=bot_message.message_id)


@dp.message(AddRufflePrizes.title)
async def input_title(message: types.Message, state: FSMContext) -> None:
	state_data = await state.get_data()

	kb = InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text="Пропустить", callback_data="ruffle_prizes_skip_description")],
			[InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
		]
	)

	bot_message = await bot.edit_message_caption(
		chat_id=message.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption="Отлично, теперь введите описание для товара.",
		reply_markup=kb,
	)
	await bot.delete_message(message.from_user.id, message.message_id)
	await state.update_data(last_bot_msg_id=bot_message.message_id, ruffle_prizes_title=message.text)
	await state.set_state(AddRufflePrizes.description)


@dp.message(AddRufflePrizes.description)
@dp.callback_query(CData("ruffle_prizes_skip_description"), AddRufflePrizes.description)
async def input_description(obj: Union[types.Message, types.CallbackQuery], state: FSMContext):
	state_data = await state.get_data()

	bot_message = await bot.edit_message_caption(
		chat_id=obj.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption="Хорошо, теперь мне нужно знать стоимость этого розыгрыша.",
		reply_markup=ikb.back_to_start
	)

	ruffle_prizes_description = None
	if isinstance(obj, types.Message):
		ruffle_prizes_description = obj.text
		await bot.delete_message(obj.from_user.id, obj.message_id)

	await state.update_data(last_bot_msg_id=bot_message.message_id, ruffle_prizes_description=ruffle_prizes_description)
	await state.set_state(AddRufflePrizes.money_needed)


@dp.message(F.text.isdigit(), AddRufflePrizes.money_needed)
async def input_money_needed(message: types.Message, state: FSMContext) -> None:
	state_data = await state.get_data()

	kb = InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text=i, callback_data=f"ruffle_prizes_time_{i}") for i in ["3", "6", "12", "24"]],
			[InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
		]
	)

	bot_message = await bot.edit_message_caption(
		chat_id=message.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption="Теперь выберите время отсчета. (Можно написть вручную количество часов)",
		reply_markup=kb,
	)

	await bot.delete_message(message.from_user.id, message.message_id)
	await state.update_data(last_bot_msg_id=bot_message.message_id, ruffle_prizes_money_needed=int(message.text))
	await state.set_state(AddRufflePrizes.countdown_hours)


@dp.callback_query(F.data.startswith("ruffle_prizes_time"))
@dp.message(F.text.isdigit(), AddRufflePrizes.countdown_hours)
async def input_time_start(obj: Union[types.Message, types.CallbackQuery], state: FSMContext) -> None:
	state_data = await state.get_data()

	if isinstance(obj, types.Message) and obj.text.isdigit():
		countdown_hours = int(obj.text)
	elif isinstance(obj, types.CallbackQuery):
		countdown_hours = int(obj.data.split("_")[-1])
	else:
		return

	kb = InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text="Пропустить", callback_data="ruffle_prizes_photos_skip")],
			[InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
		]
	)

	bot_message = await bot.edit_message_caption(
		chat_id=obj.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption="Загрузите фотографии (можно несколько)",
		reply_markup=kb,
	)

	if isinstance(obj, types.Message):
		await bot.delete_message(obj.from_user.id, obj.message_id)

	await state.update_data(last_bot_msg_id=bot_message.message_id, ruffle_prizes_countdown_hours=int(countdown_hours))
	await state.set_state(AddRufflePrizes.photos)


@dp.message(F.photo, AddRufflePrizes.photos)
@media_group_handler(only_album=False, receive_timeout=2)
async def get_photos(messages: List[types.Message], state: FSMContext) -> None:
	all_photos = []

	for message in messages:
		all_photos.append(message.photo[-1])
		await bot.delete_message(message.from_user.id, message.message_id)

	await state.update_data(ruffle_prizes_photos=all_photos)
	await get_menu_icon(messages[-1], state)


@dp.callback_query(CData("ruffle_prizes_photos_skip"), AddRufflePrizes.photos)
async def get_menu_icon(obj: Union[types.Message, types.CallbackQuery], state: FSMContext) -> None:
	state_data = await state.get_data()

	if isinstance(obj, types.CallbackQuery):
		await state.update_data(ruffle_prizes_photos=None)

	bot_message = await bot.edit_message_caption(
		chat_id=obj.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption=f"Отправьте стикер для иконки в меню",
		reply_markup=ikb.back_to_start,
	)
	await state.update_data(last_bot_msg_id=bot_message.message_id)
	await state.set_state(AddRufflePrizes.menu_icon)


@dp.message(lambda m: m.sticker is not None and m.sticker.is_animated is False, AddRufflePrizes.menu_icon)
async def view_final_ruffle_prizes(message: types.Message, state: FSMContext) -> None:
	state_data = await state.get_data()
	get_file = await bot.get_file(message.sticker.file_id)
	menu_icon = await bot.download_file(get_file.file_path)

	kb = InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text="Подтвердить", callback_data="confirm_create_ruffle_prizes")],
			[InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
		]
	)

	await bot.edit_message_caption(
		chat_id=message.from_user.id,
		message_id=state_data["last_bot_msg_id"],
		caption=f"Вы подтверждаете создание розыгрыша <b>{state_data['ruffle_prizes_title']}</b>?",
		reply_markup=kb,
	)
	await bot.delete_message(message.from_user.id, message.message_id)
	img = Photo.compress_img(menu_icon.read(), width=300, height=300, format="PNG", quality=50)
	await state.update_data(ruffle_prizes_menu_icon=img)
	await state.set_state(AddRufflePrizes.confirm)


async def task_create_ruffle_prizes(
	title: str, money_needed: int, countdown_hours: int,
	description: str = None, photos: List[PhotoSize] = None,
	menu_icon: PhotoSize = None
) -> None:

	success_photos = []
	success_low_quality_photos = []
	if photos is not None:
		for photo in photos:
			photo_file = await bot.get_file(photo.file_id)
			downloaded_photo = await bot.download_file(photo_file.file_path)
			photo = downloaded_photo.read()

			s_photo = Photo.compress_img(photo, width=800, height=600, quality=70)
			l_photo = Photo.compress_img(photo, width=40, height=30, quality=10)
			success_photos.append(s_photo)
			success_low_quality_photos.append(l_photo)
	else:
		success_photos = None

	await db.create_ruffle_prizes(
		title=title,
		description=description,
		money_needed=money_needed,
		countdown_hours=countdown_hours,
		photos=success_photos,
		low_quality_photos=success_low_quality_photos,
		menu_icon=menu_icon
	)


@dp.callback_query(CData("confirm_create_ruffle_prizes"))
async def confirm_create_ruffle_prizes(callback: types.CallbackQuery, state: FSMContext) -> None:
	state_data = await state.get_data()

	await bot.edit_message_caption(
		chat_id=callback.from_user.id,
		message_id=callback.message.message_id,
		caption=f"Розыгрыш <b>\"{state_data['ruffle_prizes_title']}\"</b> создан успешно!",
		reply_markup=ikb.back_to_start
	)
	asyncio.create_task(
		task_create_ruffle_prizes(
			title=state_data["ruffle_prizes_title"],
			description=state_data["ruffle_prizes_description"],
			money_needed=state_data["ruffle_prizes_money_needed"],
			countdown_hours=state_data["ruffle_prizes_countdown_hours"],
			photos=state_data["ruffle_prizes_photos"],
			menu_icon=state_data["ruffle_prizes_menu_icon"]
		)
	)
	await state.clear()
