from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "finex_db"
DB_PORT = 3306

SECRET_KEY = os.getenv("SECRET_KEY")

SESSION_CONFIG = {
    "SESSION_COOKIE_SAMESITE": "Lax",
    "SESSION_COOKIE_SECURE": False,
    "PERMANENT_SESSION_LIFETIME": timedelta(hours=1)
}