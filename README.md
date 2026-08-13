# 🏟 Stadion Bron Bot

Sizning sxemangiz asosida to'liq ishlaydigan Telegram bot: foydalanuvchilar stadion qidiradi,
eng yaqinini topadi, o'z stadionini qo'shadi; admin esa yangi qo'shilgan stadionlarni
tasdiqlaydi yoki rad etadi. **Bron qilish / to'lov yo'q** — sxemada belgilanganidek, faqat
ma'lumot va bo'sh vaqtlarni ko'rsatish funksiyasi bor.

## 📁 Tuzilma

```
stadion_bot/
├── main.py              # Botni ishga tushirish
├── config.py            # Sozlamalar (token, adminlar, viloyatlar)
├── database.py          # SQLite bilan ishlash (users, stadiums, photos, times)
├── keyboards.py         # Barcha klaviaturalar
├── states.py            # FSM holatlari
├── handlers/
│   ├── start.py         # /start, ro'yxatdan o'tish, bosh menyu
│   ├── home.py           # Qidirish, filtr, stadion kartochkasi
│   ├── nearest.py        # Eng yaqin stadionlar (geolokatsiya)
│   ├── add_stadium.py     # Stadion qo'shish (10 bosqichli forma)
│   ├── profile.py         # Profil, telefon/lokatsiya
│   ├── my_stadiums.py     # "Mening stadionlarim" — tahrirlash, rasmlar, vaqtlar
│   └── admin.py           # Admin panel — tasdiqlash/rad etish
├── webapp/                # (bonus) Mini-App uchun boshlang'ich sahifa
├── requirements.txt
└── .env.example
```

## ⚙️ O'rnatish

1. Python 3.10+ o'rnatilgan bo'lishi kerak.
2. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` fayli sizning bergan ma'lumotlaringiz bilan **allaqachon tayyor** — qo'shimcha
   sozlash shart emas:
   - `BOT_TOKEN` — sizning botingiz tokeni
   - `ADMIN_IDS` — sizning Telegram ID'ingiz (admin sifatida)

   Agar keyinchalik boshqa token/admin bilan ishlatmoqchi bo'lsangiz, `.env` faylini
   tahrirlang (`.env.example` — namuna sifatida saqlangan).
4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

Ma'lumotlar bazasi (`stadion.db`) birinchi ishga tushganda avtomatik yaratiladi.
Eski bazadan foydalansangiz ham, `region`/`district` ustunlari avtomatik qo'shiladi
(migratsiya `init_db()` ichida amalga oshadi).

## 🧭 Funksiyalar (yangilangan)

- **/start** — ro'yxatdan o'tish → darhol **viloyat va tuman so'raladi** (tugmalar orqali,
  xato yozishning oldini olish uchun matn kiritilmaydi) → bosh menyu
- **🏟 Stadionlar** (avvalgi «Bosh sahifa») — ochilganda **avtomatik ravishda foydalanuvchi
  tanlagan tumandagi tasdiqlangan stadionlar ro'yxati** chiqadi. Ro'yxatdan stadionni
  tanlasa — to'liq kartochka ochiladi: rasmlari, nomi, manzili, narxi, egasining telefon
  raqami, va xaritada manzilni ochish tugmasi
  - «🔎 Stadion qidirish» — nom/joy/telefon bo'yicha qidirish
  - «🔁 Tumanni o'zgartirish» — istalgan vaqt boshqa viloyat/tumanga o'tish
- **📍 Eng yaqin stadionlar** — geolokatsiya asosida masofani hisoblab, eng yaqinlarini chiqaradi
- **➕ Stadion qo'shish** — 10 bosqichli forma: nom → **viloyat (tugma)** → **tuman (tugma)**
  → manzil → lokatsiya (xaritadan tanlab yuborish, yoki keyinroq qo'shish uchun
  «⏭ O'tkazib yuborish») → telefon → narx → rasmlar → tekshirish → yuborish →
  admin tasdig'ini kutish
  - **Dublikat lokatsiya tekshiruvi**: agar bergan koordinata boshqa (tasdiqlangan yoki
    kutilayotgan) stadionnikiga juda yaqin bo'lsa (~50 metr), foydalanuvchiga ogohlantirish
    chiqadi. U «Baribir yuborish»ni tanlashi mumkin, lekin bu holda admin kartasida
    **maxsus DIQQAT belgisi** chiqadi
- **👤 Profil** — shaxsiy ma'lumot (shu jumladan tanlangan hudud), telefon/lokatsiya/hudud
  o'zgartirish, "Mening stadionlarim"
  - Har bir stadion uchun: ma'lumotlar, tahrirlash, rasmlar (qo'shish/o'chirish),
    vaqtlarni boshqarish (sana tanlab, soatlarni 🟢/🔴 qilib bosish orqali band/bo'sh qilish)

### 🔐 Admin panel (`/admin`, faqat `ADMIN_IDS` ro'yxatidagilar uchun)

Endi to'liq, tugmalar orqali boshqariladigan **yagona panel**:

- **📋 Yangi arizalar** — yangi qo'shilgan stadionlar, rasm+ma'lumot bilan:
  - ✅ Tasdiqlash — egasiga xabar boradi
  - ❌ Rad etish — **admin sababni yozadi**, bu sabab egasiga yuboriladi
  - 🗺 Xaritada tekshirish — lokatsiya to'g'ri belgilanganini xaritadan tekshirish
- **🏟 Barcha stadionlar** — statusi bo'yicha (kutilmoqda/tasdiqlangan/rad etilgan)
  ro'yxatdan istalgan stadionni ko'rish, xaritadan tekshirish va **butunlay o'chirish**
  (o'chirilganda egasiga xabar boradi)
- **🔎 Stadion qidirish** — statusidan qat'i nazar, nom/manzil/telefon bo'yicha qidirish
- **📊 Statistika** — jami foydalanuvchilar, jami/kutilayotgan/tasdiqlangan/rad etilgan
  stadionlar soni
- **📢 Ommaviy xabar** — barcha foydalanuvchilarga matn/rasm/video ko'rinishida xabar
  (reklama) yuborish, oldindan ko'rish va tasdiqlash bilan (`/xabar` buyrug'i orqali ham
  ishlaydi)

### 📍 Lokatsiya yuborishda muammo bo'lsa

Agar Telegram «joriy joylashuvni aniqlay olmadi» desa, bu — qurilma/ilova ruxsati
masalasi (bot kodiga bog'liq emas). Bot endi bu holatda foydalanuvchiga yo'l-yo'riq
ko'rsatadi:
- Telefon: **Sozlamalar → Ilovalar → Telegram → Ruxsatlar → Joylashuv → Ruxsat berish**
- Stadion joyi boshqa manzilda bo'lsa: xabar yozish maydoni yonidagi **📎 (skrepka) →
  Location → xaritadan nuqta tanlab → Send Selected Location**
- Yoki hozircha «⏭ O'tkazib yuborish»ni bosib, keyin qo'shib qo'yish mumkin

## 🌐 Mini-App haqida (bonus, ixtiyoriy)

To'liq Telegram Mini-App (WebApp) qilish uchun quyidagilar zarur:
1. **HTTPS'da joylashgan veb-sahifa** (bepul: GitHub Pages, Vercel, Railway va h.k.)
2. Bot tugmasiga `WebAppInfo(url="https://...")` qo'shish
3. Sahifa botning ma'lumotlar bazasidan JSON API orqali stadionlarni olib, xarita/kartochka
   ko'rinishida chiqarishi kerak (masalan Flask + shu SQLite fayl)

Bu qism serverga joylashtirishni talab qilgani uchun ("qiyin" qism), hozircha botning o'zi
barcha funksiyalarni to'liq (inline tugmalar, kartochkalar, rasm galereyasi bilan) ta'minlaydi —
foydalanuvchi tajribasi deyarli mini-app kabi qulay. `webapp/index.html` da oddiy namuna bor;
xohlasangiz, uni Flask backend bilan to'liq mini-appga aylantirib beraman — shunchaki ayting.

## 🗄 Ma'lumotlar bazasi sxemasi

Sizning sxemangizdagi 4 ta jadval aynan shu ko'rinishda amalga oshirilgan:
`users`, `stadiums`, `stadium_photos`, `stadium_times`.

## 🚫 Qilinmaydigan funksiyalar (sxemaga muvofiq)

- Foydalanuvchi bron qilmaydi, online bron/to'lov yo'q
- Foydalanuvchi vaqtni o'zi band qila olmaydi
- Foydalanuvchi (egasi bo'lmasa) stadion ma'lumotini o'zgartira olmaydi
