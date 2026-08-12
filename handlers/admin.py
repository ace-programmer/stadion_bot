from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import database as db
import keyboards as kb
from config import ADMIN_IDS

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda admin huquqi yo'q.")
        return
    pending = db.get_pending_stadiums()
    if not pending:
        await message.answer("✅ Tasdiqlash kutayotgan stadionlar yo'q.")
        return
    await message.answer(f"🔐 Admin panel — {len(pending)} ta yangi stadion:")
    for s in pending:
        await send_review_card(message, s)


async def send_review_card(message: Message, s):
    owner_row = None
    cur = db._conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
    owner_row = cur.fetchone()
    photos = db.get_stadium_photos(s["id"])
    text = (
        f"🏟 <b>{s['name']}</b>\n"
        f"👤 Egasi: {owner_row['full_name'] if owner_row else '—'} "
        f"(@{owner_row['username'] if owner_row and owner_row['username'] else '—'})\n"
        f"📞 Telefon: {s['phone']}\n"
        f"📍 Viloyat: {s['region']}\n"
        f"📍 Tuman: {s['district']}\n"
        f"🏠 Manzil: {s['address']}\n"
        f"📍 Lokatsiya: {s['latitude']}, {s['longitude']}\n"
        f"💰 Narx: {s['price']:,} so'm\n"
        f"📸 Rasmlar: {len(photos)} ta"
    )
    if photos:
        await message.answer_photo(photos[0]["file_id"], caption=text, reply_markup=kb.admin_review_kb(s["id"]))
    else:
        await message.answer(text, reply_markup=kb.admin_review_kb(s["id"]))


@router.callback_query(F.data.startswith("admapprove:"))
async def approve_stadium(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    stadium_id = int(call.data.split(":")[1])
    db.set_stadium_status(stadium_id, "approved")
    await call.answer("✅ Tasdiqlandi")
    await call.message.edit_caption(caption=(call.message.caption or "") + "\n\n✅ TASDIQLANDI") if call.message.caption else await call.message.edit_text((call.message.text or "") + "\n\n✅ TASDIQLANDI")

    s = db.get_stadium(stadium_id)
    cur = db._conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
    owner = cur.fetchone()
    if owner:
        try:
            await bot.send_message(owner["telegram_id"], f"✅ Sizning «{s['name']}» stadioningiz tasdiqlandi va endi foydalanuvchilarga ko'rinadi!")
        except Exception:
            pass


@router.callback_query(F.data.startswith("admreject:"))
async def reject_stadium(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    stadium_id = int(call.data.split(":")[1])
    db.set_stadium_status(stadium_id, "rejected")
    await call.answer("❌ Rad etildi")
    await call.message.edit_caption(caption=(call.message.caption or "") + "\n\n❌ RAD ETILDI") if call.message.caption else await call.message.edit_text((call.message.text or "") + "\n\n❌ RAD ETILDI")

    s = db.get_stadium(stadium_id)
    cur = db._conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
    owner = cur.fetchone()
    if owner:
        try:
            await bot.send_message(owner["telegram_id"], f"❌ Sizning «{s['name']}» stadioningiz rad etildi. Ma'lumotlarni tekshirib qayta yuborishingiz mumkin.")
        except Exception:
            pass
