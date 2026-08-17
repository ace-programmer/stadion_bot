from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import ProfileState

router = Router()


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user_by_tg(message.from_user.id)
    text = (
        "👤 <b>Shaxsiy ma'lumotlar</b>\n\n"
        f"Ism: {user['full_name']}\n"
        f"Username: @{user['username'] if user['username'] else '—'}\n"
        f"Telegram ID: {user['telegram_id']}\n"
        f"📞 Telefon: {user['phone'] or '—'}\n"
        f"📍 Joylashuv: {'✅ mavjud' if user['latitude'] else '—'}\n"
        f"🏘 Hudud: {user['region'] or '—'}, {user['district'] or '—'}"
    )
    await message.answer(text, reply_markup=kb.profile_menu())


@router.callback_query(F.data == "profile_phone")
async def ask_phone(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(ProfileState.waiting_phone)
    await call.message.answer(
        "📱 Telefon raqamingizni yuboring:", reply_markup=kb.phone_request_kb()
    )


@router.message(ProfileState.waiting_phone, F.contact)
async def save_phone_contact(message: Message, state: FSMContext):
    db.update_user_phone(message.from_user.id, message.contact.phone_number)
    await state.clear()
    await message.answer("✅ Telefon raqam saqlandi.", reply_markup=kb.main_menu())


@router.message(ProfileState.waiting_phone, F.text)
async def save_phone_text(message: Message, state: FSMContext):
    if message.text.strip() == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    db.update_user_phone(message.from_user.id, message.text.strip())
    await state.clear()
    await message.answer("✅ Telefon raqam saqlandi.", reply_markup=kb.main_menu())


@router.callback_query(F.data == "profile_location")
async def ask_location(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(ProfileState.waiting_location)
    await call.message.answer(
        "📍 Joylashuvingizni yuboring.\n\n"
        "📵 Agar «joriy joylashuvni aniqlay olmadi» degan xato chiqsa — telefon sozlamalarida "
        "Telegram ilovasiga joylashuv (location) ruxsatini bering.",
        reply_markup=kb.location_request_kb(show_skip=True),
    )


@router.message(ProfileState.waiting_location, F.location)
async def save_location(message: Message, state: FSMContext):
    db.update_user_location(
        message.from_user.id, message.location.latitude, message.location.longitude
    )
    await state.clear()
    await message.answer("✅ Joylashuv saqlandi.", reply_markup=kb.main_menu())


@router.message(ProfileState.waiting_location, F.text)
async def cancel_or_skip_location(message: Message, state: FSMContext):
    await state.clear()
    if message.text.strip() == "⏭ O'tkazib yuborish":
        await message.answer("⏭ O'tkazib yuborildi.", reply_markup=kb.main_menu())
    else:
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())


@router.callback_query(F.data == "my_stadiums")
async def my_stadiums(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = db.get_user_by_tg(call.from_user.id)
    stadiums = db.get_user_stadiums(user["id"], "approved")
    if not stadiums:
        await call.message.answer(
            "✅ Tasdiqlangan stadioningiz hozircha yo'q.\n\n"
            "Agar yaqinda stadion qo'shgan bo'lsangiz, admin tasdiqlashini kuting — "
            "tasdiqlangach shu yerda ko'rinadi. Yangi stadion qo'shish uchun "
            "«➕ Stadion qo'shish» tugmasidan foydalaning."
        )
        return
    await call.message.answer(
        f"🏟 Sizning tasdiqlangan stadionlaringiz ({len(stadiums)} ta):",
        reply_markup=kb.stadium_list_kb(stadiums),
    )


@router.callback_query(F.data == "profile_district")
async def change_profile_district(call: CallbackQuery, state: FSMContext):
    await call.answer()
    from handlers.district import start_district_select

    await start_district_select(call, state, purpose="profile")


@router.callback_query(F.data == "profile_favorites")
async def show_favorites(call: CallbackQuery):
    await call.answer()
    favs = db.get_user_favorite_stadiums(call.from_user.id)
    if not favs:
        await call.message.answer(
            "❤️ Sevimlilar ro'yxati hozircha bo'sh.\n\n"
            "Istalgan stadion kartochkasida «🤍 Sevimlilarga» tugmasini bosib qo'shishingiz mumkin."
        )
        return
    await call.message.answer(
        f"❤️ Sevimli stadionlaringiz ({len(favs)} ta):",
        reply_markup=kb.stadium_list_kb(favs, prefix="viewstadium"),
    )
