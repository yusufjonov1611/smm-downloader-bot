import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from handlers import main_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Render yoki Uptime monitoring uchun sog'lomlik tekshiruvi (Health Check)."""
    return web.Response(text="SMM Downloader Bot is running smoothly! 🚀")

async def start_web_server():
    """Render.com uchun HTTP portni ochish (Render Web Service talabi)."""
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check veb-server {port}-portda ishga tushdi.")

async def set_bot_commands(bot: Bot):
    """Telegram menyusidagi komandalarni to'g'irlash."""
    user_commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish"),
        BotCommand(command="help", description="💡 Botdan foydalanish qo'llanmasi"),
        BotCommand(command="contact", description="💬 Admin bilan aloqa / Muhokama")
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    if ADMIN_ID:
        admin_commands = user_commands + [
            BotCommand(command="admin", description="⚙️ Admin panel boshqaruvi")
        ]
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
        except Exception as e:
            logger.warning(f"Admin komandalarini o'rnatishda ogohlantirish: {e}")

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")
        return

    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await init_db()

    # Render.com portini ochish
    await start_web_server()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_router(main_router)
    await set_bot_commands(bot)

    logger.info("Bot muvaffaqiyatli ishga tushdi!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
