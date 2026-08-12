from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import REGIONS, DISTRICTS, DAY_HOURS


def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🏟 Stadionlar")
    kb.button(text="📍 Eng yaqin stadionlar")
    kb.button(text="➕ Stadion qo'shish")
    kb.button(text="👤 Profil")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)


def home_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔎 Stadion qidirish")
    kb.button(text="🔁 Tumanni o'zgartirish")
    kb.button(text="⬅️ Orqaga")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)


def cancel_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Bekor qilish")
    return kb.as_markup(resize_keyboard=True)


def location_request_kb(label: str = "📍 Joylashuvimni yuborish", show_skip: bool = False):
    kb = ReplyKeyboardBuilder()
    kb.button(text=label, request_location=True)
    if show_skip:
        kb.button(text="⏭ O'tkazib yuborish")
    kb.button(text="❌ Bekor qilish")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def phone_request_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📞 Raqamni yuborish", request_contact=True)
    kb.button(text="❌ Bekor qilish")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def regions_inline(prefix="region"):
    kb = InlineKeyboardBuilder()
    for r in REGIONS:
        kb.button(text=r, callback_data=f"{prefix}:{r}")
    kb.button(text="⬅️ Bekor qilish", callback_data=f"{prefix}:cancel")
    kb.adjust(2)
    return kb.as_markup()


def districts_inline(region: str, prefix="district"):
    kb = InlineKeyboardBuilder()
    districts = DISTRICTS.get(region, [])
    for d in districts:
        kb.button(text=d, callback_data=f"{prefix}:{d}")
    kb.button(text="⬅️ Bekor qilish", callback_data=f"{prefix}:cancel")
    kb.adjust(2)
    return kb.as_markup()


def stadium_card_kb(stadium_id: int, phone: str, lat, lon):
    kb = InlineKeyboardBuilder()
    kb.button(text="📞 Bog'lanish", callback_data=f"call:{stadium_id}")
    if lat and lon:
        kb.button(text="🗺 Manzilni ochish", url=f"https://maps.google.com/?q={lat},{lon}")
    kb.adjust(2)
    return kb.as_markup()


def results_nav_kb(idx: int, total: int, prefix: str):
    kb = InlineKeyboardBuilder()
    if idx > 0:
        kb.button(text="⬅️ Oldingi", callback_data=f"{prefix}:{idx-1}")
    kb.button(text=f"{idx+1}/{total}", callback_data="noop")
    if idx < total - 1:
        kb.button(text="Keyingi ➡️", callback_data=f"{prefix}:{idx+1}")
    kb.adjust(3)
    return kb.as_markup()


def add_stadium_photos_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tayyor", callback_data="photos_done")
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yuborish", callback_data="confirm_submit")
    kb.button(text="❌ Bekor qilish", callback_data="confirm_cancel")
    kb.adjust(2)
    return kb.as_markup()


def profile_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Telefon qo'shish/o'zgartirish", callback_data="profile_phone")
    kb.button(text="📍 Joylashuv qo'shish/o'zgartirish", callback_data="profile_location")
    kb.button(text="🏘 Hududni o'zgartirish", callback_data="profile_district")
    kb.button(text="🏟 Mening stadionlarim", callback_data="my_stadiums")
    kb.adjust(1)
    return kb.as_markup()


def my_stadiums_status_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⏳ Tasdiqlash kutilmoqda", callback_data="mystatus:pending")
    kb.button(text="✅ Tasdiqlangan", callback_data="mystatus:approved")
    kb.button(text="❌ Rad etilgan", callback_data="mystatus:rejected")
    kb.adjust(1)
    return kb.as_markup()


def stadium_list_kb(stadiums, prefix="pickstadium"):
    kb = InlineKeyboardBuilder()
    for s in stadiums:
        kb.button(text=f"🏟 {s['name']}", callback_data=f"{prefix}:{s['id']}")
    kb.adjust(1)
    return kb.as_markup()


def stadium_manage_kb(stadium_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏟 Ma'lumotlar", callback_data=f"sinfo:{stadium_id}")
    kb.button(text="✏️ O'zgartirish", callback_data=f"sedit:{stadium_id}")
    kb.button(text="📸 Rasmlar", callback_data=f"sphotos:{stadium_id}")
    kb.button(text="🕐 Vaqtlar", callback_data=f"stimes:{stadium_id}")
    kb.adjust(1)
    return kb.as_markup()


def edit_fields_kb(stadium_id: int):
    kb = InlineKeyboardBuilder()
    fields = [
        ("Nom", "name"),
        ("Telefon", "phone"),
        ("Narx", "price"),
        ("Manzil", "address"),
    ]
    for label, field in fields:
        kb.button(text=label, callback_data=f"editfield:{stadium_id}:{field}")
    kb.button(text="📍 Lokatsiya", callback_data=f"editlocation:{stadium_id}")
    kb.adjust(2)
    return kb.as_markup()


def photos_manage_kb(stadium_id: int, photos):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Rasm qo'shish", callback_data=f"addphoto:{stadium_id}")
    for i, p in enumerate(photos, 1):
        kb.button(text=f"🗑 {i}-rasmni o'chirish", callback_data=f"delphoto:{p['id']}:{stadium_id}")
    kb.adjust(1)
    return kb.as_markup()


def times_menu_kb(stadium_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Sana tanlash", callback_data=f"pickdate:{stadium_id}")
    kb.adjust(1)
    return kb.as_markup()


def hours_kb(stadium_id: int, date: str, busy_map: dict):
    kb = InlineKeyboardBuilder()
    for t in DAY_HOURS:
        busy = busy_map.get(t, 0)
        icon = "🔴" if busy else "🟢"
        kb.button(text=f"{icon} {t}", callback_data=f"toggletime:{stadium_id}:{date}:{t}")
    kb.adjust(4)
    return kb.as_markup()


def admin_review_kb(stadium_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"admapprove:{stadium_id}")
    kb.button(text="❌ Rad etish", callback_data=f"admreject:{stadium_id}")
    kb.adjust(2)
    return kb.as_markup()
