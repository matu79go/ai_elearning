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

# クイズ設定
# 1セッションあたりの出題数。テストしたい時はここを直接変更
QUIZ_QUESTIONS_PER_SESSION = 10

# 小テスト (Drill) 設定
# N連続正解で完了扱い。最初は3、慣れたら5等に調整
DRILL_STREAK_TO_MASTER = 3
# ドリル完了時に付与するポイント
DRILL_COMPLETION_POINTS = 5

# 宿題 (Assignment) 設定
# material/subject単位でも1セッションはこの問題数で区切る
# (「もう一度」で次のN問が出る仕組み)
ASSIGNMENT_QUESTIONS_PER_SESSION = 15
