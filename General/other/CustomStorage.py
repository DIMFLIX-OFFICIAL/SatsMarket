import asyncio
import pickle

import asyncpg
import jsonpickle as jsonpickle
from asyncio import AbstractEventLoop

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Dict, Optional, Any
from General.db import DictRecord

class PGStorage(BaseStorage):
    __slots__ = ("host", "port", "username", "password", "database", "dsn", "loop")

    def __init__(self) -> None:
        self._db = None

    async def create_connection_and_tables(self, db: asyncpg.Connection) -> None:
        await db.execute("""CREATE TABLE IF NOT EXISTS aiogram_state(
                            "key" TEXT NOT NULL PRIMARY KEY,
                            "state" TEXT)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS aiogram_data(
                            "key" TEXT NOT NULL PRIMARY KEY,
                            "data" TEXT)""")

        self._db = db

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        state = state.state if isinstance(state, State) else state
        await self._db.execute(
            """
            INSERT INTO aiogram_state VALUES($1, $2)
            ON CONFLICT (key) DO UPDATE SET state = $2
            """,
            str(key.user_id), state
        )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        response = await self._db.fetchval("SELECT state FROM aiogram_state WHERE key=$1", str(key.user_id))
        return response

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        print("Set data ", data)
        await self._db.execute(
            """
            INSERT INTO aiogram_data VALUES($1, $2)
            ON CONFLICT (key) DO UPDATE SET data = $2
            """,
            str(key.user_id), jsonpickle.dumps(data)
        )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        response = await self._db.fetchval("SELECT data FROM aiogram_data WHERE key=$1", str(key.user_id))
        print("Get data", response)
        return jsonpickle.loads(response)

    async def close(self) -> None:
        pass
