from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from handlers.district import start_district_select

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    row = db.get_or_create_user(user.id, user.username or "", user.full_name or "")

    await message.answer(
        f"Assalomu alaykum, {user.full_name}! 👋\n\n"
        "🏟 <b>Stadion Bron Bot</b>ga xush kelibsiz.\n"
        "Bu yerda siz stadionlarni qidirishingiz, eng yaqinlarini topishingiz "
        "va o'z stadioningizni ro'yxatga qo'shishingiz mumkin.",
    )

    if not row["region"] or not row["district"]:
        await start_district_select(message, state, purpose="register")
    else:
        await message.answer("Bosh menyu:", reply_markup=kb.main_menu())


@router.message(F.text == "⬅️ Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=kb.main_menu())


@router.message(F.text == "❌ Bekor qilish")
async def cancel_any(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.main_menu())
