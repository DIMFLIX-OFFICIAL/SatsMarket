from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from BotCore.handlers import start
from General.loader import bot, dp, db
from BotCore.keyboards import ikb
from BotCore.filters.callback_filters import CData
from BotCore.utils.payment import Payment


class PaySt(StatesGroup):
    amount = State()
    check_pay = State()


@dp.callback_query(CData("balance_top_up"))
async def start_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    last_bot_msg = await bot.edit_message_caption(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        caption="Ok, send me amount UAH",
        reply_markup=ikb.back_to_start
    )
    await state.set_state(PaySt.amount)
    await state.update_data(last_bot_msg_id=last_bot_msg.message_id)


@dp.message(F.text.isdigit(), PaySt.amount)
async def send_invoice(message: types.Message, state: FSMContext) -> None:
    sd = await state.get_data()
    payment_data = await Payment.get_invoice(message.from_user.id, float(message.text))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Проверить платёж", callback_data="check_pay"),
            InlineKeyboardButton(text="Оплатить", url=payment_data["url"])
        ],
        [InlineKeyboardButton(text="В главное меню", callback_data="back_to_start")]
    ])

    last_bot_msg = await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=sd["last_bot_msg_id"],
        caption="Вот ваш инвойс, прошу, оплачивайте!",
        reply_markup=kb
    )
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
    await state.update_data(payment_data=payment_data, last_bot_msg_id=last_bot_msg.message_id)
    await state.set_state(PaySt.check_pay)


@dp.callback_query(CData("check_pay"), PaySt.check_pay)
async def check_pay(callback: types.CallbackQuery, state: FSMContext) -> None:
    sd = await state.get_data()
    order_id = sd["payment_data"]["order_id"]
    order_info = await Payment.get_order_info(order_id)

    if order_info["type"] == "success":
        if order_info["status"] in ["success", "hold"]:
            await bot.answer_callback_query(
                callback_query_id=callback.id,
                text=f"🟢 Баланс пополнен на {order_info['amount']} {order_info['currency']}"
            )
            await db.update_payment_order_when_completed(order_id)
            await start.callback_start_handler(callback, state)
            return

        else:
            await bot.answer_callback_query(
                callback_query_id=callback.id,
                text=f"🔴 Вы еще не оплатили счёт"
            )

    else:
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=f"🔴 Не удалось получить информацию по счёту"
        )

    await state.set_state(PaySt.check_pay)
