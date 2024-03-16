from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from BotCore.filters.callback_filters import CData
from BotCore.utils.photos_manager import Photo
from General.loader import bot, dp
from BotCore.keyboards import ikb


@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=await Photo.file(),
        caption="Приветствую, рад тебя видеть, " + message.from_user.first_name,
        reply_markup=ikb.start_menu
    )
    await bot.delete_message(message.from_user.id, message.message_id)


@dp.callback_query(CData("back_to_start"))
async def callback_start_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.edit_message_caption(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        caption="Приветствую, рад тебя видеть, " + callback.from_user.first_name,
        reply_markup=ikb.start_menu
    )


@dp.callback_query(CData("hide_message"))
async def hide_message(callback: types.CallbackQuery):
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


