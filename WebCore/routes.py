import datetime
import decimal
import hashlib
import hmac
import json
from typing import Union

from aiogram.client.session import aiohttp
from aiogram.utils.web_app import safe_parse_webapp_init_data, WebAppInitData
from aiohttp import web, WSMessage
from aiohttp.web_request import Request
import aiohttp_jinja2
import jinja2
from loguru import logger

from BotCore.utils.photos_manager import Photo
from General import config as cfg
from General.db_settings import DictRecord
from General.loader import bot, db


class WebRoutes:
    def __init__(self, webapp: web.Application) -> None:
        self.webapp = webapp
        aiohttp_jinja2.setup(webapp, enable_async=True, loader=jinja2.FileSystemLoader('WebCore/templates'))
        self.webapp.router.add_static('/static/', path='WebCore/static', name='static')
        webapp.router.add_post("/payment_notify", self.payment_notify)
        webapp.router.add_get("/giveaway", self.giveaway_get)
        webapp.router.add_post("/giveaway", self.giveaway_post)
        webapp.router.add_get("/giveaway/ws", self.websocket)

    async def payment_notify(self, request: web.Request) -> None:
        data = await request.post()
        logger.info(f"Получено уведомление об оплате с данными {data}")

        ##==> Проверка на ip address
        ################################################
        async with aiohttp.ClientSession() as s:
            response = await s.get('https://aaio.io/api/public/ips', timeout=10)
            good_ip_list = (await response.json())["list"]
            user_ip = request.headers["X-Forwarded-For"]

            if user_ip not in good_ip_list:
                logger.error(f"{user_ip} не входит в {good_ip_list}")
                return

        ##==> Проверка на подпись
        ################################################
        for i in ["order_id", "sign", "amount", "currency"]:
            if i not in data:
                logger.error(f"В данных не хватает поля {i}")
                return

        order = await db.get_payment_order(int(data['order_id']))
        logger.info(f"Достали order из бд: {order}")
        if order is None: return
        sign = hashlib.sha256(':'.join([
            str(cfg.PAYMENT_MERCHANT_ID),
            "{0:.2f}".format(float(order['amount'])),
            str(order['currency']),
            str(cfg.PAYMENT_SECRET_2),
            str(order['id'])
        ]).encode('utf-8')).hexdigest()

        logger.info(f"Получили подпись {sign}")
        if not hmac.compare_digest(data['sign'], sign):
            logger.error(f"Подпись из уведомления ({data['sign']}) не совпадает с нашей")
            return

        await db.update_payment_order_when_completed(order["id"])

    @staticmethod
    async def check_auth(auth_data: str) -> Union[WebAppInitData, None]:
        try:
            return safe_parse_webapp_init_data(token=cfg.BOT_TOKEN, init_data=auth_data)
        except ValueError:
            return None

    @staticmethod
    async def render_template(path: str, request: Request, **kwargs):
        return await aiohttp_jinja2.render_template_async(path, request, context=kwargs)

    @staticmethod
    def post_wrapper(func):
        async def inner(*args, **kwargs):

            def json_encoder(obj):
                if isinstance(obj, datetime.datetime):
                    return obj.isoformat()
                elif isinstance(obj, DictRecord):
                    return obj.to_dict()
                elif isinstance(obj, decimal.Decimal):
                    return int(obj)

                raise TypeError(f"{obj} is not JSON serializable")

            result = await func(*args, **kwargs)
            return web.json_response(result, dumps=lambda obj: json.dumps(obj, default=json_encoder))

        return inner

    @post_wrapper
    async def giveaway_post(self, request: web.Request) -> dict:
        data = await request.json()
        user_data = await self.check_auth(data["Authorization"]) if "Authorization" in data else None

        if "method" not in data:
            return dict(ok=False, error="Параметра method не существует!")

        match data["method"]:
            case "get_user_data":
                if user_data is None:
                    return dict(ok=False, error="Такого пользователя не существует!")

                user_data: WebAppInitData
                user_info = await db.get_user(user_data.user.id)
                user_photo = await Photo.avatar(bot, user_data.user.id)
                user_photo = Photo.compress_img(user_photo.data, quality=70, width=100, height=100)
                return dict(
                    ok=True,
                    firstname=user_data.user.first_name,
                    balance=user_info["balance"],
                    photo=user_photo
                )

            case "get_prize_draws":
                if "type" in data:
                    if data["type"] == "active":
                        prize_draws = await db.get_active_prize_draws()
                    elif data["type"] == "participate":
                        prize_draws = await db.get_participate_prize_draws(user_data.user.id)
                    elif data["type"] == "closed":
                        prize_draws = await db.get_closed_prize_draws()
                    else:
                        prize_draws = await db.get_prize_draws()
                else:
                    prize_draws = await db.get_prize_draws()

                return dict(ok=True, prize_draws=prize_draws)

            case "load_high_quality_photos":
                prize_draws = await db.get_high_quality_photos()
                return dict(ok=True, prize_draws=prize_draws)

            case "get_user_bets":
                if user_data is None:
                    return dict(ok=False, error="Такого пользователя не существует!")

                bets = await db.get_user_bets(user_data.user.id)
                return dict(ok=True, bets=None if bets == [] else bets)

            case "create_draw_prizes_bet":
                if user_data is None:
                    return dict(ok=False, error="Такого пользователя не существует!")

                if "bet" not in data or "draw_id" not in data:
                    return dict(ok=False, error="Поля \"bet\" и \"draw_id\" должны быть заполнены!")
                else:
                    if not str(data["draw_id"]).isdigit() or not str(data["bet"]).isdigit():
                        return dict(ok=False, error="Поля \"bet\" и \"draw_id\" должны быть числами!")
                    else:
                        draw_id = int(data["draw_id"])
                        bet = int(data["bet"])

                if_draw_exists: bool = await db.if_active_draw_exists(draw_id)

                if if_draw_exists:
                    user_balance: int = (await db.get_user(user_data.user.id))["balance"]
                    if user_balance >= bet:
                        await db.change_balance(user_data.user.id, "-", bet)
                        created_bet = await db.create_bet(user_data.user.id, bet, draw_id)
                        return dict(ok=True, new_balance=user_balance - bet, bet=created_bet)
                    else:
                        return dict(ok=False, error="Недостаточно баланса для совершения данной ставки!")
                else:
                    return dict(ok=False, error="Такого розыгрыша не существует!")

            case _:
                return dict(ok=False, error=f"Метода {data['method']} не существует!")

    async def giveaway_get(self, request):
        return await self.render_template('app.html', request)

    async def websocket(self, request: Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            async for msg in ws:
                msg: WSMessage
                data_message = json.loads(msg.data)

                if msg.type == aiohttp.WSMsgType.TEXT:
                    ...

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' % ws.exception())

        finally:
            pass

        return ws
