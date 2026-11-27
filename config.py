import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "6169032422").strip()
try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 6169032422

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
SUPPORT_CHAT_LINK = os.getenv("SUPPORT_CHAT_LINK", "").strip()

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "bot_database.sqlite3"

# Telegram Bot API max file size is 50MB (52428800 bytes)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
