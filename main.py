import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import load_config
from bot.database import Database
from bot.handlers import routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def set_main_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="sell", description="Разместить анкету (Продать)"),
        BotCommand(command="buy", description="Найти анкету (Купить)"),
        BotCommand(command="my_ads", description="Мои размещенные анкеты"),
        BotCommand(command="help", description="Справка и помощь"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]
    await bot.set_my_commands(commands)


async def main():
    config = load_config()

    if not config.bot_token:
        logger.error(
            "BOT_TOKEN не задан! Создайте файл .env на основе .env.example и укажите токен вашего бота."
        )
        sys.exit(1)

    # Initialize Database
    db = Database(config.db_name)
    await db.init()
    logger.info(f"База данных SQLite инициализирована ({config.db_name})")

    # Initialize Bot & Dispatcher
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Provide dependencies to handlers
    dp["db"] = db
    dp["config"] = config

    # Register all routers
    for router in routers:
        dp.include_router(router)

    # Set Telegram bot menu commands
    try:
        await set_main_commands(bot)
    except Exception as e:
        logger.warning(f"Не удалось установить команды бота: {e}")

    # Delete webhook to prevent conflicts with polling
    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()
    logger.info(f"Бот успешно запущен: @{bot_info.username} (ID: {bot_info.id})")
    if config.channel_id:
        logger.info(f"Канал для публикации объявлений: {config.channel_id}")
    else:
        logger.warning(
            "CHANNEL_ID не указан в .env! Публикация в канал отключена."
        )

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
