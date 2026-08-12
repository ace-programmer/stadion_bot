from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from handlers.home import send_stadium_card

router = Router()


@router.message(F.text == "📍 Eng yaqin stadionlar")
async def ask_location(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Eng yaqin stadionlarni topish uchun joriy joylashuvingizni yuboring.\n\n"
        "📵 Agar «joriy joylashuvni aniqlay olmadi» degan xato chiqsa — telefon sozlamalarida "
        "Telegram ilovasiga joylashuv (location) ruxsatini bering:\n"
        "Sozlamalar → Ilovalar → Telegram → Ruxsatlar → Joylashuv → Ruxsat berish.",
        reply_markup=kb.location_request_kb(),
    )


@router.message(F.location)
async def process_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    db.update_user_location(message.from_user.id, lat, lon)

    nearest = db.get_nearest_stadiums(lat, lon, limit=10)
    await message.answer("Bosh menyu:", reply_markup=kb.main_menu())
    if not nearest:
        await message.answer("❌ Hozircha yaqin atrofda stadionlar mavjud emas.")
        return

    await message.answer(f"📍 Sizga eng yaqin {len(nearest)} ta stadion:")
    for dist, s in nearest:
        await send_stadium_card(message, s)
        await message.answer(f"📏 Masofa: {dist:.1f} km")
