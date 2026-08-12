from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import DistrictSelect

router = Router()


async def start_district_select(message_or_call, state: FSMContext, purpose: str):
    """purpose: 'register' (ro'yxatdan o'tishda) yoki 'change' (keyin o'zgartirishda)"""
    await state.update_data(purpose=purpose)
    await state.set_state(DistrictSelect.region)
    text = "🌍 Qaysi viloyatdagi stadionlarni ko'rmoqchisiz? Viloyatni tanlang:"
    if hasattr(message_or_call, "message"):
        await message_or_call.message.answer(text, reply_markup=kb.regions_inline("distregion"))
    else:
        await message_or_call.answer(text, reply_markup=kb.regions_inline("distregion"))


@router.callback_query(DistrictSelect.region, F.data.startswith("distregion:"))
async def region_chosen(call: CallbackQuery, state: FSMContext):
    region = call.data.split(":", 1)[1]
    await call.answer()
    if region == "cancel":
        await state.clear()
        await call.message.edit_text("Bekor qilindi.")
        return
    await state.update_data(region=region)
    await state.set_state(DistrictSelect.district)
    await call.message.edit_text(f"Viloyat: {region}")
    await call.message.answer(
        "Endi tumaningizni/shahringizni tanlang:",
        reply_markup=kb.districts_inline(region, "distdistrict"),
    )


@router.callback_query(DistrictSelect.district, F.data.startswith("distdistrict:"))
async def district_chosen(call: CallbackQuery, state: FSMContext):
    district = call.data.split(":", 1)[1]
    await call.answer()
    data = await state.get_data()
    if district == "cancel":
        await state.clear()
        await call.message.edit_text("Bekor qilindi.")
        return

    region = data.get("region")
    purpose = data.get("purpose", "register")
    db.update_user_region_district(call.from_user.id, region, district)
    await state.clear()
    await call.message.edit_text(f"📍 Tanlangan hudud: {region}, {district}")

    if purpose == "register":
        await call.message.answer(
            "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
            "🏟 <b>Stadionlar</b> bo'limida siz shu tumandagi stadionlarni ko'rasiz. "
            "Xohlasangiz «🔁 Tumanni o'zgartirish» orqali istalgan vaqt o'zgartirishingiz mumkin.",
            reply_markup=kb.main_menu(),
        )
    elif purpose == "profile":
        await call.message.answer("✅ Hududingiz yangilandi.", reply_markup=kb.main_menu())
    else:
        # Yangi tuman tanlangach, o'sha tumandagi stadionlar ro'yxatini ko'rsatamiz
        from handlers.home import show_district_stadiums

        await show_district_stadiums(call.message, region, district)
