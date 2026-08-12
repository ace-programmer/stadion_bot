from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import AddStadium
from config import ADMIN_IDS

router = Router()


@router.message(F.text == "➕ Stadion qo'shish")
async def start_add(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddStadium.name)
    await message.answer(
        "🏟 Yangi stadion qo'shish.\n\n1️⃣ Stadion nomini kiriting:",
        reply_markup=kb.cancel_kb(),
    )


@router.message(AddStadium.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddStadium.region)
    await message.answer("2️⃣ Viloyatni tanlang:", reply_markup=kb.regions_inline("addregion"))


@router.callback_query(AddStadium.region, F.data.startswith("addregion:"))
async def get_region(call: CallbackQuery, state: FSMContext):
    region = call.data.split(":", 1)[1]
    await call.answer()
    if region == "cancel":
        await state.clear()
        await call.message.edit_text("Bekor qilindi.")
        return
    await state.update_data(region=region)
    await state.set_state(AddStadium.district)
    await call.message.edit_text(f"Viloyat: {region}")
    await call.message.answer(
        "3️⃣ Tuman/shaharni tanlang:", reply_markup=kb.districts_inline(region, "adddistrict")
    )


@router.callback_query(AddStadium.district, F.data.startswith("adddistrict:"))
async def get_district(call: CallbackQuery, state: FSMContext):
    district = call.data.split(":", 1)[1]
    await call.answer()
    if district == "cancel":
        await state.clear()
        await call.message.edit_text("Bekor qilindi.")
        return
    await state.update_data(district=district)
    await state.set_state(AddStadium.address)
    await call.message.edit_text(f"Tuman/shahar: {district}")
    await call.message.answer("4️⃣ Manzil / mo'ljalni kiriting:", reply_markup=kb.cancel_kb())


@router.message(AddStadium.address)
async def get_address(message: Message, state: FSMContext):
    if message.text.strip() == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    await state.update_data(address=message.text.strip())
    await state.set_state(AddStadium.location)
    await message.answer(
        "5️⃣ Endi stadion joylashgan nuqtani xaritadan tanlab yuboring.\n\n"
        "❗️ <b>Muhim:</b> pastdagi tugma sizning hozirgi turgan joyingizni yuboradi. "
        "Agar stadion boshqa manzilda bo'lsa:\n"
        "1. Xabar yozish maydoni yonidagi 📎 (skrepka) belgisini bosing\n"
        "2. «Location» / «Joylashuv» ni tanlang\n"
        "3. Xaritani surib, kerakli nuqtani bosib, «Send Selected Location»ni tanlang\n\n"
        "📵 <b>«Joriy joylashuvni aniqlay olmadi» xatosi chiqsa:</b> telefon sozlamalarida "
        "Telegram ilovasiga joylashuv (location) ruxsatini bering: "
        "Sozlamalar → Ilovalar → Telegram → Ruxsatlar → Joylashuv → Ruxsat berish. "
        "Kompyuterdan foydalansangiz, brauzer/Telegram Desktop'ga geolokatsiya ruxsatini bering.\n\n"
        "Hozircha lokatsiyani qo'ymoqchi bo'lmasangiz, «⏭ O'tkazib yuborish»ni bosing "
        "— keyin profil orqali qo'shib qo'yishingiz mumkin.",
        reply_markup=kb.location_request_kb("📍 Stadion joylashuvini yuborish", show_skip=True),
    )


@router.message(AddStadium.location, F.location)
async def get_location(message: Message, state: FSMContext):
    await state.update_data(
        latitude=message.location.latitude, longitude=message.location.longitude
    )
    await state.set_state(AddStadium.phone)
    await message.answer(
        "6️⃣ Asosiy telefon raqamni yuboring:", reply_markup=kb.phone_request_kb()
    )


@router.message(AddStadium.location, F.text)
async def get_location_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    if text == "⏭ O'tkazib yuborish":
        await state.update_data(latitude=None, longitude=None)
        await state.set_state(AddStadium.phone)
        await message.answer(
            "⏭ Lokatsiyasiz davom etamiz (keyin «Mening stadionlarim» orqali qo'shib qo'yishingiz mumkin).\n\n"
            "6️⃣ Asosiy telefon raqamni yuboring:",
            reply_markup=kb.phone_request_kb(),
        )
        return
    await message.answer(
        "❗️ Iltimos, pastdagi tugmalardan foydalaning yoki 📎 orqali xaritadan joy tanlab yuboring."
    )


@router.message(AddStadium.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(AddStadium.price)
    await message.answer("7️⃣ 1 soatlik narxni kiriting (faqat raqam, so'm):", reply_markup=kb.cancel_kb())


@router.message(AddStadium.phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    await state.update_data(phone=text)
    await state.set_state(AddStadium.price)
    await message.answer("7️⃣ 1 soatlik narxni kiriting (faqat raqam, so'm):", reply_markup=kb.cancel_kb())


@router.message(AddStadium.price)
async def get_price(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("❗️ Iltimos, faqat raqam kiriting. Masalan: 150000")
        return
    await state.update_data(price=int(text), photos=[])
    await state.set_state(AddStadium.photos)
    await message.answer(
        "8️⃣ Stadion rasmlarini yuboring (1 tadan 5 tagacha). "
        "Tugatgach «✅ Tayyor» tugmasini bosing:",
        reply_markup=kb.add_stadium_photos_kb(),
    )


@router.message(AddStadium.photos, F.photo)
async def get_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 5:
        await message.answer("❗️ Maksimal 5 ta rasm yuklashingiz mumkin. «✅ Tayyor» tugmasini bosing.")
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(
        f"✅ {len(photos)}-rasm qabul qilindi. Yana yuborishingiz mumkin yoki «✅ Tayyor»ni bosing.",
        reply_markup=kb.add_stadium_photos_kb(),
    )


@router.callback_query(AddStadium.photos, F.data == "photos_done")
async def photos_done(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    text = (
        "9️⃣ Ma'lumotlarni tekshiring:\n\n"
        f"🏟 Nom: {data.get('name')}\n"
        f"📍 Viloyat: {data.get('region')}\n"
        f"📍 Tuman: {data.get('district')}\n"
        f"🏠 Manzil: {data.get('address')}\n"
        f"📞 Telefon: {data.get('phone')}\n"
        f"💰 Narx: {data.get('price'):,} so'm\n"
        f"📸 Rasmlar: {len(data.get('photos', []))} ta"
    )
    await state.set_state(AddStadium.confirm)
    await call.message.answer(text, reply_markup=kb.confirm_kb())


@router.callback_query(AddStadium.confirm, F.data == "confirm_cancel")
async def confirm_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("Bosh menyu:", reply_markup=kb.main_menu())


@router.callback_query(AddStadium.confirm, F.data == "confirm_submit")
async def confirm_submit(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = db.get_user_by_tg(call.from_user.id)
    stadium_id = db.create_stadium(user["id"], data)
    for i, file_id in enumerate(data.get("photos", [])):
        db.add_stadium_photo(stadium_id, file_id, i)
    await state.clear()
    await call.answer()
    await call.message.edit_text("⏳ Stadioningiz admin tasdig'ini kutmoqda. Rahmat!")
    await call.message.answer("Bosh menyu:", reply_markup=kb.main_menu())

    # Adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 Yangi stadion tasdiqlash uchun yuborildi:\n"
                f"🏟 {data.get('name')}\n📍 {data.get('region')}, {data.get('district')}\n"
                f"arizangiz adminga yuborildi. Tasdiqlangandan so'ng, stadion foydalanuvchilarga ko'rinadi. \n\n",
                f"Admin: @ace_programmer\n",
            )
        except Exception:
            pass
