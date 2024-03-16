import asyncio
from datetime import datetime

import asyncpg
from typing import List

import jsonpickle
from loguru import logger

from .db_settings import DbSettings, DictRecord


class Database(DbSettings):
	def __init__(self, host: str, port: int, username: str, password: str, db_name: str):
		self.db_auth_data = dict(host=host, port=port, user=username, password=password)
		self.db_name = db_name
		self.db: asyncpg.Pool = None

	async def create_connection(self) -> asyncpg.Pool:
		try:
			self.db = await asyncpg.create_pool(**self.db_auth_data, database=self.db_name, record_class=DictRecord)
		except asyncpg.exceptions.InvalidCatalogNameError:
			async with asyncpg.create_pool(**self.db_auth_data) as conn:
				await conn.execute(f"CREATE DATABASE \"{self.db_name}\"")
			self.db = await asyncpg.create_pool(**self.db_auth_data, database=self.db_name, record_class=DictRecord)

		await self.create_tables(self.db)

	async def get_user(self, user_id: int) -> dict:
		return await self.db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)

	async def add_user(self, user_id: int, username: str) -> dict:
		user = await self.db.fetchrow("INSERT INTO users(id, username) VALUES ($1, $2) RETURNING *", user_id, username)
		logger.info(f"New User added - {user_id} | {username}")
		return user

	async def update_user_online(self, user_id: int, latest_online: datetime) -> dict:
		user = await self.db.execute("UPDATE users SET latest_online=$1 WHERE id=$2 RETURNING *", latest_online, user_id)
		return user

	async def count_users(self) -> int:
		response = await self.db.fetchval("SELECT COUNT(*) FROM users")
		return response

	async def create_ruffle_prizes(
			self, title: str, money_needed: int, countdown_hours: int,
			description: str = None, photos: List[str] = None, low_quality_photos: List[str] = None,
			menu_icon: str = None) -> None:
		photos = None if photos is None else jsonpickle.dumps(photos)
		low_quality_photos = None if low_quality_photos is None else jsonpickle.dumps(low_quality_photos)
		description = "Описание отсутствует..." if description is None else description
		await self.db.execute("""
			INSERT INTO ruffle_prizes (title, description, money_needed, countdown_hours, 
			photos, low_quality_photos, menu_icon) VALUES ($1, $2, $3, $4, $5, $6, $7)
		""", title, description, money_needed, countdown_hours, photos, low_quality_photos, menu_icon)

	async def get_prize_draws(self) -> List[dict]:
		return await self.db.fetch(f"""
			SELECT RP.id, title, description, COALESCE(SUM(B.amount), 0) AS money_collected, money_needed,
			low_quality_photos, NULL as photos, menu_icon, countdown_hours, countdown_start_time, winner_id, is_over
			FROM ruffle_prizes RP, bets B 
			WHERE RP.id=B.ruffle_prizes_id 
			GROUP BY RP.id
		""")

	async def get_high_quality_photos(self):
		return await self.db.fetch("SELECT id, photos FROM ruffle_prizes")

	async def get_active_prize_draws(self) -> List[dict]:
		return await self.db.fetch("""
			SELECT RP.id, title, description, COALESCE(SUM(B.amount), 0) AS money_collected, money_needed,
			low_quality_photos, NULL as photos, menu_icon, countdown_hours, countdown_start_time, winner_id, is_over
			FROM ruffle_prizes RP
			LEFT JOIN bets B ON RP.id=B.ruffle_prizes_id 
			WHERE RP.is_over=false 
			GROUP BY RP.id
		""")

	async def get_participate_prize_draws(self, user_id: int) -> List[dict]:
		return await self.db.fetch("""
			SELECT RP.id, title, description, COALESCE(SUM(B.amount), 0) AS money_collected, money_needed,
			low_quality_photos, NULL as photos, menu_icon, countdown_hours, countdown_start_time, winner_id, is_over
			FROM ruffle_prizes RP
			LEFT JOIN bets B ON RP.id=B.ruffle_prizes_id 
			WHERE RP.is_over=false 
			AND RP.id IN (SELECT ruffle_prizes_id FROM bets WHERE user_id=$1) 
			GROUP BY RP.id
		""", user_id)

	async def get_closed_prize_draws(self) -> List[dict]:
		return await self.db.fetch("""
			SELECT 
			RP.id, title, description, COALESCE(SUM(B.amount), 0) AS money_collected, 
			money_needed, low_quality_photos, NULL as photos, menu_icon, countdown_hours, 
			countdown_start_time, winner_id, is_over,
			CASE WHEN EXISTS (SELECT 1 FROM bets WHERE ruffle_prizes_id = RP.id) THEN (
				SELECT jsonb_object_agg(B.user_id, B.amount) FROM (
					SELECT user_id, SUM(amount) AS amount
					FROM bets
					WHERE ruffle_prizes_id = RP.id
					GROUP BY user_id
			  	) AS B
			) ELSE NULL END AS users_bets
			FROM ruffle_prizes RP
			LEFT JOIN bets B ON RP.id=B.ruffle_prizes_id 
			WHERE RP.is_over=true 
			GROUP BY RP.id
		""")

	async def if_active_draw_exists(self, draw_id):
		return await self.db.fetchval("SELECT EXISTS (SELECT 1 FROM ruffle_prizes WHERE id=$1)", draw_id)

	async def create_bet(self, user_id, amount, ruffle_prizes_id) -> dict:
		new_bet =  await self.db.fetchrow("""
			INSERT INTO bets(user_id, amount, ruffle_prizes_id) VALUES ($1, $2, $3) 
			RETURNING id as bet_id, amount as bet_amount, bet_time, 
			ruffle_prizes_id, (SELECT title as ruffle_prizes_title FROM ruffle_prizes WHERE id=$3)
			""", user_id, amount, ruffle_prizes_id
		)
		asyncio.create_task(self.db.execute("""
			UPDATE ruffle_prizes SET countdown_start_time=NOW()
			WHERE id=$1 
			AND (SELECT SUM(amount) FROM bets WHERE ruffle_prizes_id=$1) >= money_needed 
			AND countdown_start_time IS NULL 
			""", ruffle_prizes_id
		))

		return new_bet

	async def get_user_bets(self, user_id) -> List[dict]:
		return await self.db.fetch("""
			SELECT B.id as bet_id, b.amount as bet_amount,
			b.bet_time, B.ruffle_prizes_id, 
			RP.title AS ruffle_prizes_title
			FROM bets B, ruffle_prizes RP WHERE B.ruffle_prizes_id=RP.id AND B.user_id=$1
		""", user_id)

	async def change_balance(self, user_id: int, operation: str, amount: int) -> bool:
		balance = await self.db.fetchval("SELECT balance FROM users WHERE id=$1", user_id)

		match operation:
			case "+":
				balance += amount,
			case "-":
				balance = balance - amount,
			case "=":
				balance = amount
			case _:
				return False

		await self.db.execute("UPDATE users SET balance=$1 WHERE id=$2", balance[0], user_id)
		return True

	async def create_order_in_payment(self, user_id: int, amount: int, currency: str) -> int:
		order_id = await self.db.fetchval(
			"INSERT INTO payment(user_id, amount, currency) VALUES($1, $2, $3) RETURNING id",
			user_id, amount, currency
		)
		return order_id

	async def update_payment_order_when_completed(self, order_id: int) -> None:
		await self.db.execute("""
			WITH updated_users AS (
				UPDATE users
				SET balance = balance + payment.amount, latest_online = now()
				FROM payment
				WHERE payment.user_id = users.id AND payment.id = $1 AND payment.is_payed = false
					AND NOT EXISTS (SELECT 1 FROM payment WHERE payment.user_id = users.id AND payment.id = $1 AND payment.is_payed = true)
				RETURNING users.id
			)
			UPDATE payment SET is_payed = true
			WHERE payment.user_id IN (SELECT id FROM updated_users) AND payment.id = $1 AND payment.is_payed = false;
		""", order_id)

	async def get_payment_order(self, order_id: int) -> dict:
		response = await self.db.fetchrow("SELECT * FROM payment WHERE id=$1", order_id)
		return response



