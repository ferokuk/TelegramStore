import os
import sys
from pathlib import Path

from src.logger import logger

MEDIA_ROOT_BOT = Path("/django_app")
DJANGO_PATH = Path("/django_app")


def setup_django():
    # 1. Добавляем путь в sys.path
    sys.path.insert(0, str(DJANGO_PATH))

    # 2. Проверка существования settings.py
    settings_path = DJANGO_PATH / "TelegramStore" / "settings.py"
    if not settings_path.exists():
        logger.error(f"Файл настроек не найден: {settings_path}")
        raise ImportError("Django settings not found")

    # 3. Настройка Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TelegramStore.settings")

    try:
        import django
        django.setup()
        logger.info("✅ Django успешно инициализирован")
        return True
    except Exception as e:
        logger.exception(f"❌ Ошибка инициализации Django: {e}")
        return False
