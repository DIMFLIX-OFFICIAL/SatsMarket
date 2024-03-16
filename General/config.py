from pyngrok import ngrok
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN: str = env.str('BOT_TOKEN')
ADMIN_ID: int = env.int('ADMIN_ID')

PAYMENT_MERCHANT_ID: str = env.str('PAYMENT_MERCHANT_ID')
PAYMENT_API_KEY: str = env.str("PAYMENT_API_KEY")
PAYMENT_SECRET_1: str = env.str("PAYMENT_SECRET_1")
PAYMENT_SECRET_2: str = env.str("PAYMENT_SECRET_2")
PAYMENT_CURRENCY: str = "UAH"
PAYMENT_FORM_LANG: str = "ua"

DB_HOST: str = env.str("DB_HOST")
DB_PORT: int = env.int("DB_PORT")
DB_USERNAME: str = env.str("DB_USERNAME")
DB_PASSWORD: str = env.str("DB_PASSWORD")
DB_NAME: str = env.str("DB_NAME")

WEBHOOK_HOST: str = env.str("WEBHOOK_HOST", default='localhost')
WEBHOOK_PORT: int = env.int("WEBHOOK_PORT", default=5000)
WEBHOOK_PATH: str = env.str("WEBHOOK_PATH")
WEB_URL: str = ngrok.connect(WEBHOOK_PORT).public_url if env.bool("AUTO_URL", default=False) else env.str("WEB_URL")

DEBUG_LOGGING: bool = env.bool("DEBUG_LOGGING", default=True)
