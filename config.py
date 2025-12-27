# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

load_dotenv()

TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))

raw_admin_ids = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in raw_admin_ids.split(',') if id.strip()]
if OWNER_ID not in ADMIN_IDS: ADMIN_IDS.append(OWNER_ID)

# Weather Defaults
DEFAULT_LAT = 51.4982
DEFAULT_LON = 31.2893
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Chernihiv')

# RSS Config
raw_feeds = os.getenv('RSS_FEEDS', '')
RSS_FEEDS = [url.strip() for url in raw_feeds.split(',') if url.strip()]

# Network Monitoring
MONITOR_TARGETS = int(os.getenv('MONITORING_TARGETS', 0))
