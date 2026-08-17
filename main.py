import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from scheduler import reminder_scheduler, backup_scheduler

from handlers import start, home, nearest, add_stadium, profile, my_stadiums, admin, district

logging.basicConfig(level=logging.INFO)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylida BOT_TOKEN='...' ni to'ldiring.")

    db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(district.router)
    dp.include_router(add_stadium.router)
    dp.include_router(home.router)
    dp.include_router(nearest.router)
    dp.include_router(profile.router)
    dp.include_router(my_stadiums.router)

    await bot.delete_webhook(drop_pending_updates=True)

    # Fon vazifalari: jadval eslatmasi va haftalik zaxira nusxa
    asyncio.create_task(reminder_scheduler(bot))
    asyncio.create_task(backup_scheduler(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
