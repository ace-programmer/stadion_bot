from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import EditStadium, ManagePhotos, ManageTimes

router = Router()

STATUS_LABELS = {
    "pending": "⏳ Tasdiqlash kutilmoqda",
    "approved": "✅ Tasdiqlangan",
    "rejected": "❌ Rad etilgan",
}


def _is_owner(stadium, user_row):
    return stadium and user_row and stadium["owner_id"] == user_row["id"]


async def _is_text_field(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    return data.get("field") != "location"


async def _is_location_field(message: Message, state: FSMContext) -> bool:
    data = await state.get_data()
    return data.get("field") == "location"


@router.callback_query(F.data.startswith("mystatus:"))
async def list_by_status(call: CallbackQuery):
    status = call.data.split(":")[1]
    await call.answer()
    user = db.get_user_by_tg(call.from_user.id)
    stadiums = db.get_user_stadiums(user["id"], status)
    if not stadiums:
        await call.message.answer(f"{STATUS_LABELS[status]}: bo'sh.")
        return
    await call.message.answer(
        f"{STATUS_LABELS[status]} ({len(stadiums)} ta):",
        reply_markup=kb.stadium_list_kb(stadiums),
    )


@router.callback_query(F.data.startswith("pickstadium:"))
async def pick_stadium(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    s = db.get_stadium(stadium_id)
    if not s:
        await call.message.answer("Topilmadi.")
        return
    await call.message.answer(
        f"🏟 <b>{s['name']}</b> — {STATUS_LABELS.get(s['status'], s['status'])}",
        reply_markup=kb.stadium_manage_kb(stadium_id),
    )


@router.callback_query(F.data.startswith("sinfo:"))
async def stadium_info(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    s = db.get_stadium(stadium_id)
    photos = db.get_stadium_photos(stadium_id)
    text = (
        f"🏟 Nom: {s['name']}\n"
        f"📍 Viloyat: {s['region']}\n"
        f"📍 Tuman: {s['district']}\n"
        f"🏠 Manzil: {s['address']}\n"
        f"📍 Lokatsiya: {s['latitude']}, {s['longitude']}\n"
        f"📞 Telefon: {s['phone']}\n"
        f"💰 Narx: {s['price']:,} so'm\n"
        f"📸 Rasmlar: {len(photos)} ta\n"
        f"Status: {STATUS_LABELS.get(s['status'], s['status'])}"
    )
    await call.message.answer(text)


# ---------------- EDIT INFO ----------------

@router.callback_query(F.data.startswith("sedit:"))
async def edit_menu(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    await call.message.answer("✏️ Qaysi maydonni o'zgartirmoqchisiz?", reply_markup=kb.edit_fields_kb(stadium_id))


@router.callback_query(F.data.startswith("editfield:"))
async def edit_field_ask(call: CallbackQuery, state: FSMContext):
    _, stadium_id, field = call.data.split(":")
    await call.answer()
    await state.set_state(EditStadium.waiting_value)
    await state.update_data(stadium_id=int(stadium_id), field=field)
    await call.message.answer(f"Yangi qiymatni kiriting ({field}):", reply_markup=kb.cancel_kb())


@router.message(EditStadium.waiting_value, F.text, _is_text_field)
async def edit_field_save(message: Message, state: FSMContext):
    if message.text.strip() == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    data = await state.get_data()
    stadium_id = data["stadium_id"]
    field = data["field"]
    value = message.text.strip()
    if field == "price":
        clean = value.replace(" ", "").replace(",", "")
        if not clean.isdigit():
            await message.answer("❗️ Faqat raqam kiriting.")
            return
        value = int(clean)
    db.update_stadium_field(stadium_id, field, value)
    await state.clear()
    await message.answer("✅ Yangilandi.", reply_markup=kb.main_menu())


@router.callback_query(F.data.startswith("editlocation:"))
async def edit_location_ask(call: CallbackQuery, state: FSMContext):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    await state.set_state(EditStadium.waiting_value)
    await state.update_data(stadium_id=stadium_id, field="location")
    await call.message.answer(
        "📍 Yangi lokatsiyani yuboring.\n\n"
        "❗️ Stadion joyi hozirgi turgan joyingizdan farq qilsa, 📎 (skrepka) → «Location» → "
        "xaritadan kerakli nuqtani tanlab «Send Selected Location»ni bosing. "
        "Aynan shu yerda tursangiz, pastdagi tugmadan foydalaning.\n\n"
        "📵 «Joriy joylashuvni aniqlay olmadi» xatosi chiqsa — Telegram ilovasiga "
        "joylashuv ruxsatini bering (Sozlamalar → Ilovalar → Telegram → Ruxsatlar → Joylashuv).",
        reply_markup=kb.location_request_kb("📍 Stadion joylashuvini yuborish", show_skip=True),
    )


@router.message(EditStadium.waiting_value, F.location, _is_location_field)
async def edit_location_save(message: Message, state: FSMContext):
    data = await state.get_data()
    stadium_id = data["stadium_id"]
    db.update_stadium_field(stadium_id, "latitude", message.location.latitude)
    db.update_stadium_field(stadium_id, "longitude", message.location.longitude)
    await state.clear()
    await message.answer("✅ Lokatsiya yangilandi.", reply_markup=kb.main_menu())


@router.message(EditStadium.waiting_value, F.text, _is_location_field)
async def edit_location_text_fallback(message: Message, state: FSMContext):
    await state.clear()
    if message.text.strip() == "⏭ O'tkazib yuborish":
        await message.answer("⏭ O'tkazib yuborildi.", reply_markup=kb.main_menu())
    else:
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())


# ---------------- PHOTOS ----------------

@router.callback_query(F.data.startswith("sphotos:"))
async def photos_menu(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    photos = db.get_stadium_photos(stadium_id)
    await call.message.answer(
        f"📸 Rasmlar ({len(photos)} ta):", reply_markup=kb.photos_manage_kb(stadium_id, photos)
    )


@router.callback_query(F.data.startswith("addphoto:"))
async def add_photo_ask(call: CallbackQuery, state: FSMContext):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    photos = db.get_stadium_photos(stadium_id)
    if len(photos) >= 5:
        await call.message.answer("❗️ Maksimal 5 ta rasm bo'lishi mumkin.")
        return
    await state.set_state(ManagePhotos.waiting_photo)
    await state.update_data(stadium_id=stadium_id)
    await call.message.answer("📸 Yangi rasmni yuboring:", reply_markup=kb.cancel_kb())


@router.message(ManagePhotos.waiting_photo, F.photo)
async def add_photo_save(message: Message, state: FSMContext):
    data = await state.get_data()
    stadium_id = data["stadium_id"]
    photos = db.get_stadium_photos(stadium_id)
    db.add_stadium_photo(stadium_id, message.photo[-1].file_id, len(photos))
    await state.clear()
    await message.answer("✅ Rasm qo'shildi.", reply_markup=kb.main_menu())


@router.callback_query(F.data.startswith("delphoto:"))
async def delete_photo(call: CallbackQuery):
    _, photo_id, stadium_id = call.data.split(":")
    db.delete_stadium_photo(int(photo_id))
    await call.answer("🗑 O'chirildi")
    photos = db.get_stadium_photos(int(stadium_id))
    await call.message.edit_text(
        f"📸 Rasmlar ({len(photos)} ta):", reply_markup=kb.photos_manage_kb(int(stadium_id), photos)
    )


# ---------------- TIMES ----------------

@router.callback_query(F.data.startswith("stimes:"))
async def times_menu(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    await call.message.answer("🕐 Vaqtlarni boshqarish:", reply_markup=kb.times_menu_kb(stadium_id))


@router.callback_query(F.data.startswith("pickdate:"))
async def ask_date(call: CallbackQuery, state: FSMContext):
    stadium_id = int(call.data.split(":")[1])
    await state.clear()
    await call.answer()
    text = "📅 Sanani tanlang:"
    reply_kb = kb.dates_inline(stadium_id)
    if call.message.text and "sanasi uchun vaqtlar" in call.message.text:
        await call.message.edit_text(text, reply_markup=reply_kb)
    else:
        await call.message.answer(text, reply_markup=reply_kb)


@router.callback_query(F.data.startswith("pickdate2:"))
async def show_hours(call: CallbackQuery):
    _, stadium_id, date_str = call.data.split(":")
    stadium_id = int(stadium_id)
    await call.answer()

    times = db.get_times_for_date(stadium_id, date_str)
    busy_map = {t["time"]: t["is_busy"] for t in times}
    text = f"📋 {date_str} sanasi uchun vaqtlar (🟢 bo'sh / 🔴 band). Bosing — holati o'zgaradi:"
    reply_kb = kb.hours_kb(stadium_id, date_str, busy_map)
    if call.message.text and ("sanani tanlang" in call.message.text.lower() or "sanasi uchun vaqtlar" in call.message.text):
        await call.message.edit_text(text, reply_markup=reply_kb)
    else:
        await call.message.answer(text, reply_markup=reply_kb)


@router.callback_query(F.data.startswith("toggletime:"))
async def toggle_time(call: CallbackQuery):
    # maxsplit=3 MUHIM: vaqt qiymati ("09:00") o'zi tarkibida ":" bor,
    # oddiy split(":") bilan bo'lsa noto'g'ri bo'linib, saqlanmay qolar edi.
    _, stadium_id, date_str, time_str = call.data.split(":", 3)
    stadium_id = int(stadium_id)
    db.toggle_time_slot(stadium_id, date_str, time_str)
    times = db.get_times_for_date(stadium_id, date_str)
    busy_map = {t["time"]: t["is_busy"] for t in times}
    new_state = busy_map.get(time_str, 0)
    await call.answer("🔴 Band qilindi" if new_state else "🟢 Bo'shatildi")
    await call.message.edit_reply_markup(reply_markup=kb.hours_kb(stadium_id, date_str, busy_map))
