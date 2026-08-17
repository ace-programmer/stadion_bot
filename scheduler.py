import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import FSInputFile

import database as db
from config import ADMIN_IDS, DB_PATH

logger = logging.getLogger(__name__)

REMINDER_DELAY_HOURS = 24  # stadion tasdiqlangandan necha soat o'tgach eslatiladi
CHECK_INTERVAL_SECONDS = 3600  # har soatda tekshiradi
BACKUP_INTERVAL_SECONDS = 7 * 24 * 3600  # 1 hafta


async def check_schedule_reminders(bot: Bot):
    """Tasdiqlangan, lekin hali jadval kiritilmagan stadionlar egalariga
    bir martalik eslatma yuboradi (spam qilmaydi)."""
    stadiums = db.get_approved_stadiums_needing_reminder()
    now = datetime.now()

    for s in stadiums:
        try:
            created = datetime.fromisoformat(s["created_at"])
        except (ValueError, TypeError):
            continue

        if (now - created).total_seconds() < REMINDER_DELAY_HOURS * 3600:
            continue  # hali vaqti kelmagan

        cur = db._conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
        owner = cur.fetchone()

        if owner:
            try:
                await bot.send_message(
                    owner["telegram_id"],
                    f"🔔 Eslatma: «{s['name']}» stadioningiz tasdiqlangan, lekin hali "
                    "bo'sh/band vaqtlar jadvali kiritilmagan.\n\n"
                    "Foydalanuvchilar stadionni ko'rganda to'liq ma'lumot olishi uchun "
                    "jadvalni to'ldiring: 👤 Profil → Mening stadionlarim → stadionni "
                    "tanlang → 🕐 Vaqtlar.",
                )
            except Exception as e:
                logger.warning(f"Eslatma yuborilmadi (owner_id={owner['telegram_id']}): {e}")

        # Har holda belgilaymiz - muvaffaqiyatsiz bo'lsa ham qayta-qayta urinib
        # spam qilmasligi uchun (owner botni bloklagan bo'lishi mumkin)
        db.mark_reminder_sent(s["id"])


async def reminder_scheduler(bot: Bot):
    """Fon vazifasi - doimiy ishlab, vaqti-vaqti bilan tekshirib turadi."""
    while True:
        try:
            await check_schedule_reminders(bot)
        except Exception as e:
            logger.error(f"Eslatma tekshiruvida xatolik: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


# ---------------- HAFTALIK ZAXIRA NUSXA ----------------

async def send_db_backup(bot: Bot):
    """Ma'lumotlar bazasini adminlarga fayl sifatida yuboradi."""
    try:
        filename = f"stadion_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
        doc = FSInputFile(DB_PATH, filename=filename)
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_document(
                    admin_id,
                    doc,
                    caption=(
                        "💾 <b>Haftalik zaxira nusxa</b>\n\n"
                        "Bu faylni xavfsiz joyda saqlang. Zarurat tug'ilsa, uni "
                        "serverdagi `stadion.db` fayli o'rniga qo'yish orqali "
                        "ma'lumotlarni tiklash mumkin."
                    ),
                )
            except Exception as e:
                logger.warning(f"Backup yuborilmadi (admin_id={admin_id}): {e}")
    except Exception as e:
        logger.error(f"Backup fayli tayyorlashda xatolik: {e}")


async def backup_scheduler(bot: Bot):
    """Fon vazifasi - haftada bir marta bazani adminlarga yuboradi.
    Oxirgi yuborilgan vaqt bazaning o'zida saqlanadi, shuning uchun server
    qayta ishga tushsa ham, hafta to'lmagan bo'lsa qayta yubormaydi."""
    while True:
        try:
            last = db.get_setting("last_backup_at")
            now = datetime.now()
            should_send = True
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                    if (now - last_dt).total_seconds() < BACKUP_INTERVAL_SECONDS:
                        should_send = False
                except ValueError:
                    pass

            if should_send:
                await send_db_backup(bot)
                db.set_setting("last_backup_at", now.isoformat())
        except Exception as e:
            logger.error(f"Backup tekshiruvida xatolik: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
