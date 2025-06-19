import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = os.getenv("BOT_ID")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS").split(",")]  