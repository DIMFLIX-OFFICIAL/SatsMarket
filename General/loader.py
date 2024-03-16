import sys

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from General import config as cfg
from General.db import Database
from .other.CustomStorage import PGStorage


db = Database(cfg.DB_HOST, cfg.DB_PORT, cfg.DB_USERNAME, cfg.DB_PASSWORD, cfg.DB_NAME)
bot: Bot = Bot(token=cfg.BOT_TOKEN, parse_mode="HTML")
mem_storage = PGStorage()
dp: Dispatcher = Dispatcher(storage=mem_storage)

logger.remove()
logger.add(sys.stderr, level="DEBUG" if cfg.DEBUG_LOGGING else "INFO")
