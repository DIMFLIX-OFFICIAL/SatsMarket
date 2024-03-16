import asyncio
import random

from aiogram.webhook.aiohttp_server import TokenBasedRequestHandler
from aiohttp import web
from loguru import logger

from BotCore import handlers
from BotCore.middlewares.add_users import AddUserMiddleware
from General import config as cfg
from General.loader import bot, dp, db, mem_storage
from WebCore.routes import WebRoutes


async def tracing_the_end_of_draws():
    while True:
        draws = await db.db.fetch("""
            UPDATE ruffle_prizes
            SET is_over = TRUE
            WHERE is_over = FALSE 
            AND EXTRACT(EPOCH FROM (NOW() - countdown_start_time))/3600 >= countdown_hours
            RETURNING id;
        """)

        for draw in draws:
            draw_id = draw["id"]
            bets = await db.db.fetch(
                "SELECT user_id, SUM(amount) AS amount FROM bets WHERE ruffle_prizes_id=$1 GROUP BY user_id",
                draw_id
            )

            user_bets_result = {i["user_id"]: int(i["amount"]) for i in bets}
            ids = list(user_bets_result.keys())
            weights = list(user_bets_result.values())
            winner_id = random.choices(ids, weights=weights)[0]
            await db.db.execute("UPDATE ruffle_prizes SET winner_id=$1 WHERE id=$2", winner_id, draw_id)

        await asyncio.sleep(2)


async def on_startup(_):
    await db.create_connection()
    await mem_storage.create_connection_and_tables(db.db)
    dp.update.middleware(AddUserMiddleware())
    TokenBasedRequestHandler(dp).register(webapp, cfg.WEBHOOK_PATH)
    await bot.set_webhook(url=cfg.WEB_URL + cfg.WEBHOOK_PATH.format(bot_token=cfg.BOT_TOKEN))
    asyncio.create_task(tracing_the_end_of_draws())
    logger.success("Bot started succesfully")
    logger.warning("Debug logging enabled")


async def on_shutdown(_):
    await bot.delete_webhook()
    await dp.storage.close()
    logger.warning("Bot turned off")


if __name__ == '__main__':
    webapp = web.Application()
    webapp.on_startup.append(on_startup)
    webapp.on_shutdown.append(on_shutdown)
    WebRoutes(webapp)
    web.run_app(webapp, host=cfg.WEBHOOK_HOST, port=cfg.WEBHOOK_PORT, print=logger.success("Server started"))
