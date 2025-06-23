import os
from pathlib import Path

CATEGORIES_PER_PAGE = 3
PRODUCTS_PER_PAGE = 5
YOOKASSA_PROVIDER_TOKEN = os.environ.get("YOOKASSA_PROVIDER_TOKEN")
BASE_DIR = Path(__file__).resolve().parent.parent
ORDERS_CSV_PATH = BASE_DIR / 'data' / 'orders.csv'
