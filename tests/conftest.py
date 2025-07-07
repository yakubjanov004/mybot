import sys
from pathlib import Path

# Add project root to sys.path so tests can import modules
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Minimal environment variables required for config import
import os
os.environ.setdefault("BOT_TOKEN", "123:TEST")
os.environ.setdefault("ADMIN_IDS", "1")
