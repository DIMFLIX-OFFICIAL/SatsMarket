import aiohttp
import hashlib
from urllib.parse import urlencode
from loguru import logger

from General.loader import db
from General.config import (
    PAYMENT_SECRET_1, PAYMENT_SECRET_2, PAYMENT_API_KEY,
    PAYMENT_MERCHANT_ID, PAYMENT_CURRENCY, PAYMENT_FORM_LANG
)


class Payment:
    __merchant_id: str = PAYMENT_MERCHANT_ID
    __secret_1: str = PAYMENT_SECRET_1
    __secret_2: str = PAYMENT_SECRET_2
    __api_key: str = PAYMENT_API_KEY
    _currency: str = PAYMENT_CURRENCY
    _form_lang: str = PAYMENT_FORM_LANG
    _invoice_description: str = "Order Payment"

    @classmethod
    async def get_invoice(cls, user_id: int, amount: float) -> dict:
        order_id: int = await db.create_order_in_payment(user_id, amount, cls._currency)
        sign = ":".join([cls.__merchant_id, str(amount), cls._currency, cls.__secret_1, str(order_id)])

        params = {
            'merchant_id': cls.__merchant_id,
            'amount': amount,
            'currency': cls._currency,
            'order_id': order_id,
            'sign': hashlib.sha256(sign.encode('utf-8')).hexdigest(),
            'desc': cls._invoice_description,
            'lang': 'ru'
        }

        logger.info(f"Создан новый счёт на оплату с ID - {order_id}")

        return {
            "url": "https://aaio.io/merchant/pay?" + urlencode(params),
            "order_id": order_id,
            "amount": amount,
            "currency": cls._currency,
            "user_id": user_id
        }

    @classmethod
    async def get_order_info(cls, order_id: int) -> dict:

        params = dict(merchant_id=cls.__merchant_id, order_id=order_id)
        headers = {
            'Accept': 'application/json',
            'X-Api-Key': cls.__api_key
        }

        async with aiohttp.ClientSession() as s:
            response = await s.post(
                'https://aaio.io/api/info-pay',
                data=params, headers=headers
            )

        response_json = await response.json()
        return response_json
