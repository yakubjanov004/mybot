import os
from pathlib import Path
from dotenv import load_dotenv

# Environment faylini yuklash
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database sozlamalari
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ulugbek202")
DB_NAME = os.getenv("DB_NAME", "alfaconnect_db")

# Loyiha papkalari
BASE_DIR = Path(__file__).parent.parent
LOCALES_DIR = BASE_DIR / "locales"

# Mavjud tillar
AVAILABLE_LANGUAGES = ["uz", "ru"]
DEFAULT_LANGUAGE = "uz" 