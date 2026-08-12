from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import SearchState
from handlers.district import start_district_select

router = Router()


def stadium_caption(s):
    return (
        f"🏟 <b>{s['name']}</b>\n"
        f"📍 {s['region']}, {s['district']}\n"
        f"🏠 {s['address']}\n"
        f"💰 {s['price']:,} so'm/soat\n"
        f"📞 {s['phone']}"
    )


async def send_stadium_card(message: Message, stadium):
    photos = db.get_stadium_photos(stadium["id"])
    caption = stadium_caption(stadium)
    reply_kb = kb.stadium_card_kb(
        stadium["id"], stadium["phone"], stadium["latitude"], stadium["longitude"]
    )
    if photos:
        if len(photos) == 1:
            await message.answer_photo(photos[0]["file_id"], caption=caption, reply_markup=reply_kb)
        else:
            media = [InputMediaPhoto(media=p["file_id"]) for p in photos]
            media[0].caption = caption
            await message.answer_media_group(media)
            await message.answer("Amallar:", reply_markup=reply_kb)
    else:
        await message.answer(caption, reply_markup=reply_kb)


async def show_district_stadiums(message: Message, region: str, district: str):
    stadiums = db.filter_stadiums(region=region, district=district)
    if not stadiums:
        await message.answer(
            f"❌ <b>{region}, {district}</b> hududida hozircha tasdiqlangan stadion yo'q.\n\n"
            "«🔁 Tumanni o'zgartirish» orqali boshqa hududni tanlashingiz yoki "
            "«🔎 Stadion qidirish» orqali nom bo'yicha izlashingiz mumkin.",
            reply_markup=kb.home_menu(),
        )
        return
    await message.answer(
        f"🏟 <b>{region}, {district}</b> — {len(stadiums)} ta stadion:\n"
        "Batafsil ma'lumot uchun stadionni tanlang:",
        reply_markup=kb.home_menu(),
    )
    await message.answer(
        "Ro'yxat:", reply_markup=kb.stadium_list_kb(stadiums, prefix="viewstadium")
    )


@router.message(F.text == "🏟 Stadionlar")
async def home_menu_entry(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user_by_tg(message.from_user.id)
    if not user["region"] or not user["district"]:
        await start_district_select(message, state, purpose="register")
        return
    await show_district_stadiums(message, user["region"], user["district"])


@router.message(F.text == "🔁 Tumanni o'zgartirish")
async def change_district(message: Message, state: FSMContext):
    await start_district_select(message, state, purpose="change")


@router.callback_query(F.data.startswith("viewstadium:"))
async def view_stadium(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    await call.answer()
    s = db.get_stadium(stadium_id)
    if not s:
        await call.message.answer("❌ Stadion topilmadi.")
        return
    await send_stadium_card(call.message, s)


@router.message(F.text == "🔎 Stadion qidirish")
async def ask_search_query(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_query)
    await message.answer(
        "Stadion nomi, joy nomi yoki telefon raqamini kiriting:",
        reply_markup=kb.cancel_kb(),
    )


@router.message(SearchState.waiting_query)
async def do_search(message: Message, state: FSMContext):
    if message.text.strip() == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
        return
    await state.clear()
    query = message.text.strip()
    results = db.search_stadiums(query)
    if not results:
        await message.answer("❌ Hech narsa topilmadi.", reply_markup=kb.home_menu())
        return
    await message.answer(f"🔍 {len(results)} ta natija topildi:", reply_markup=kb.home_menu())
    await message.answer(
        "Batafsil ko'rish uchun tanlang:",
        reply_markup=kb.stadium_list_kb(results[:15], prefix="viewstadium"),
    )


@router.callback_query(F.data.startswith("call:"))
async def show_phone(call: CallbackQuery):
    stadium_id = int(call.data.split(":")[1])
    s = db.get_stadium(stadium_id)
    if s:
        await call.answer(f"📞 {s['phone']}", show_alert=True)
    else:
        await call.answer("Topilmadi", show_alert=True)


@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()
