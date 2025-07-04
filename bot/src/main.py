import os
import sys
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.config import ORDERS_CSV_PATH
from src.init_django import setup_django

from src.logger import logger
from src.utils.export_orders import save_to_csv_async

dp = Dispatcher()



async def on_startup():
    if not setup_django():
        logger.error("Не удалось инициализировать Django. Выход...")
        sys.exit(1)

    try:
        from store.models import Product, Category, Cart, CartItem, Order, OrderItem, FAQ
        from users.models import TelegramUser
    except Exception as e:
        logger.error(f"Ошибка импорта: {e}. Выход...")
        sys.exit(1)

    # Регистрация хэндлеров
    from src.handlers import start, catalog, cart, faq, order
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(faq.router)
    dp.include_router(order.router)
    # Регистрация команд
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="cart", description="Показать корзину"),
        BotCommand(command="faq", description="Часто задаваемые вопросы"),
    ])
    logger.info("✅ Бот успешно запущен")


async def on_shutdown():
    logger.info("Бот остановлен")


async def main():
    logger.info("Запуск бота...")
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
