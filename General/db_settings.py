import asyncpg


class DictRecord(asyncpg.Record):
	def __getitem__(self, key):
		value = super().__getitem__(key)
		if isinstance(value, asyncpg.Record):
			return dict(value.items())
		return value

	def to_dict(self):
		return dict(super().items())

	def __repr__(self):
		return str(dict(super().items()))


class DbSettings:
	@staticmethod
	async def create_tables(db: asyncpg.Connection) -> None:
		await db.execute("""CREATE TABLE IF NOT EXISTS \"users\"(
									id BIGINT NOT NULL PRIMARY KEY,
									username TEXT,
									balance BIGINT NOT NULL DEFAULT 0,
									latest_online TIMESTAMP NOT NULL DEFAULT now(),
									registration_date TIMESTAMP NOT NULL DEFAULT now())""")
		await db.execute("""CREATE TABLE IF NOT EXISTS \"bets\"(
									id BIGSERIAL NOT NULL PRIMARY KEY,
									user_id BIGINT NOT NULL,
									amount BIGINT NOT NULL,
									bet_time TIMESTAMP NOT NULL DEFAULT now(),
									ruffle_prizes_id INTEGER NOT NULL)""")
		await db.execute("""CREATE TABLE IF NOT EXISTS \"ruffle_prizes\"(
									id BIGSERIAL NOT NULL PRIMARY KEY,
									title TEXT NOT NULL,
									description TEXT default 'Описание отсутствует...',
									low_quality_photos JSONB,
									photos JSONB,
									menu_icon TEXT NOT NULL,
									money_collected BIGINT NOT NULL DEFAULT 0,
									money_needed BIGINT NOT NULL,
									countdown_hours BIGINT NOT NULL,
									countdown_start_time TIMESTAMP,
									winner_id BIGINT,
									is_over BOOLEAN NOT NULL DEFAULT FALSE)""")
		await db.execute("""CREATE TABLE IF NOT EXISTS \"payment\"(
									id BIGSERIAL NOT NULL PRIMARY KEY,
									user_id BIGINT NOT NULL,
									amount BIGINT NOT NULL,
									currency TEXT NOT NULL,
									date TIMESTAMP NOT NULL DEFAULT now(),
									is_payed BOOLEAN NOT NULL DEFAULT False)""")




