import asyncio
import logging
import os
import sys

from pyrogram import Client
from pyrogram.errors import FloodWait

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING, DOWNLOAD_DIR
from handlers.handlers import register_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,          # Railway stderr ni error deb belgilaydi
)
logger = logging.getLogger(__name__)

try:
    import uvloop  # type: ignore
except Exception:  # pragma: no cover
    uvloop = None


async def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # User client — private kontentga kirish uchun
    user = Client(
        "user_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        no_updates=True,        # Faqat yuklash uchun, yangiliklarga obuna emas
    )

    # Bot client — foydalanuvchi bilan muloqot
    bot = Client(
        "bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        parse_mode="HTML",
    )

    register_all(bot, user)

    logger.info("🚀 Bot ishga tushmoqda...")

    # FloodWait xatosi bo'lsa, kerakli vaqt kutib qayta urinish
    while True:
        try:
            async with user, bot:
                logger.info("✅ User client ulandi")
                logger.info("✅ Bot client ulandi")
                logger.info("🤖 Bot ishlayapti. To'xtatish uchun Ctrl+C")
                await asyncio.Event().wait()   # Abadiy kutish (Railway uchun)
        except FloodWait as e:
            wait_seconds = e.value
            logger.warning(
                f"⏳ Telegram FloodWait: {wait_seconds} soniya kutilmoqda... "
                f"(Keyin avtomatik qayta ulanadi)"
            )
            await asyncio.sleep(wait_seconds + 5)   # Biroz qo'shimcha xavfsizlik uchun
            logger.info("🔄 FloodWait tugadi, qayta ulanish...")
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Bot to'xtatildi.")
            break


if __name__ == "__main__":
    if uvloop is not None:
        uvloop.install()
    asyncio.run(main())
