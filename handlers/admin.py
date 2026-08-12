from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio

import database as db
import keyboards as kb
from config import ADMIN_IDS
from states import BroadcastState

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
        await send_review_card(message.bot, message.chat.id, s)


def build_review_content(s):
    owner_row = None
    cur = db._conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
    owner_row = cur.fetchone()
    photos = db.get_stadium_photos(s["id"])
    text = (
        f"🆕 <b>Yangi stadion tasdiqlashni kutmoqda</b>\n\n"
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
    return text, photos


async def send_review_card(bot: Bot, chat_id: int, s):
    text, photos = build_review_content(s)
    if photos:
        await bot.send_photo(
            chat_id, photos[0]["file_id"], caption=text, reply_markup=kb.admin_review_kb(s["id"])
        )
    else:
        await bot.send_message(chat_id, text, reply_markup=kb.admin_review_kb(s["id"]))


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


# ---------------- BARCHA STADIONLARNI KO'RISH / O'CHIRISH ----------------

STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlangan",
    "rejected": "❌ Rad etilgan",
}


@router.message(Command("stadionlar"))
async def admin_all_stadiums(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda admin huquqi yo'q.")
        return
    await message.answer(
        "📋 Qaysi statusdagi stadionlarni ko'rmoqchisiz?", reply_markup=kb.admin_status_kb()
    )


@router.callback_query(F.data.startswith("admstatus:"))
async def admin_list_by_status(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    status = call.data.split(":")[1]
    await call.answer()
    stadiums = db.get_stadiums_by_status(status)
    if not stadiums:
        await call.message.answer(f"{STATUS_LABELS.get(status, status)}: bo'sh.")
        return
    await call.message.answer(
        f"{STATUS_LABELS.get(status, status)} ({len(stadiums)} ta):",
        reply_markup=kb.stadium_list_kb(stadiums, prefix="admview"),
    )


@router.callback_query(F.data.startswith("admview:"))
async def admin_view_stadium(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    s = db.get_stadium(stadium_id)
    if not s:
        await call.message.answer("❌ Stadion topilmadi (allaqachon o'chirilgan bo'lishi mumkin).")
        return
    text, photos = build_review_content(s)
    text += f"\n\nStatus: {STATUS_LABELS.get(s['status'], s['status'])}"
    if photos:
        await call.message.answer_photo(
            photos[0]["file_id"], caption=text, reply_markup=kb.admin_stadium_info_kb(stadium_id)
        )
    else:
        await call.message.answer(text, reply_markup=kb.admin_stadium_info_kb(stadium_id))


@router.callback_query(F.data.startswith("admdelask:"))
async def admin_delete_ask(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    s = db.get_stadium(stadium_id)
    name = s["name"] if s else "?"
    await call.message.answer(
        f"❗️ «{name}» stadionini butunlay o'chirmoqchimisiz? Bu amalni orqaga qaytarib bo'lmaydi.",
        reply_markup=kb.admin_delete_confirm_kb(stadium_id),
    )


@router.callback_query(F.data.startswith("admdelconfirm:"))
async def admin_delete_confirm(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    stadium_id = int(call.data.split(":")[1])
    s = db.get_stadium(stadium_id)
    if not s:
        await call.answer("Allaqachon o'chirilgan", show_alert=True)
        return
    name = s["name"]
    cur = db._conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (s["owner_id"],))
    owner = cur.fetchone()

    db.delete_stadium(stadium_id)
    await call.answer("🗑 O'chirildi")
    await call.message.edit_text(f"🗑 «{name}» stadioni butunlay o'chirildi.")

    if owner:
        try:
            await bot.send_message(
                owner["telegram_id"],
                f"⚠️ Sizning «{name}» stadioningiz admin tomonidan botdan o'chirib tashlandi.",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admdelcancel:"))
async def admin_delete_cancel(call: CallbackQuery):
    await call.answer("Bekor qilindi")
    await call.message.edit_text("Bekor qilindi.")


# ---------------- OMMAVIY XABAR (REKLAMA) ----------------

@router.message(Command("xabar"))
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda admin huquqi yo'q.")
        return
    await state.set_state(BroadcastState.waiting_content)
    users_count = len(db.get_all_users())
    await message.answer(
        f"📢 Barcha foydalanuvchilarga ({users_count} ta) yubormoqchi bo'lgan xabaringizni "
        "yuboring.\n\n"
        "Matn, rasm (izoh bilan), video — istalgan turda bo'lishi mumkin. "
        "Xabar aynan qanday ko'rinishda yuborsangiz, foydalanuvchilarga ham shunday ko'rinadi.\n\n"
        "Bekor qilish uchun /bekor yozing."
    )


@router.message(BroadcastState.waiting_content, Command("bekor"))
async def broadcast_cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.")


@router.message(BroadcastState.waiting_content)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastState.confirm)
    users_count = len(db.get_all_users())
    await message.answer(
        f"⬆️ Yuqoridagi xabar {users_count} ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=kb.broadcast_confirm_kb(),
    )


@router.callback_query(BroadcastState.confirm, F.data == "broadcast_send")
async def broadcast_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    data = await state.get_data()
    await state.clear()
    await call.answer()
    await call.message.edit_text("⏳ Yuborilmoqda, biroz kuting...")

    users = db.get_all_users()
    success = 0
    failed = 0
    for u in users:
        try:
            await bot.copy_message(
                chat_id=u["telegram_id"],
                from_chat_id=data["chat_id"],
                message_id=data["message_id"],
            )
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram flood-limitiga tushmaslik uchun

    await call.message.answer(
        f"✅ Xabar yuborildi: {success} ta foydalanuvchiga\n"
        f"❌ Yuborilmadi: {failed} ta (bot bloklangan yoki hisob o'chirilgan bo'lishi mumkin)"
    )


@router.callback_query(BroadcastState.confirm, F.data == "broadcast_cancel")
async def broadcast_cancel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("Bekor qilindi")
    await call.message.edit_text("Bekor qilindi.")
