# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MySQL 設定
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "db"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "elearning"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "charset": "utf8mb4",
}

# SQLAlchemy用の接続文字列
DATABASE_URL = f"mysql+mysqldb://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset=utf8mb4"

# Flask設定
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
