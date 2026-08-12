import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin telegram ID'lari, vergul bilan ajratilgan: "123456,789012"
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x
]

DB_PATH = os.getenv("DB_PATH", "stadion.db")

REGIONS = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Andijon",
    "Farg'ona",
    "Namangan",
    "Samarqand",
    "Buxoro",
    "Xorazm",
    "Navoiy",
    "Qashqadaryo",
    "Surxondaryo",
    "Jizzax",
    "Sirdaryo",
    "Qoraqalpog'iston",
]

# Har bir viloyat/shahar uchun tumanlar ro'yxati
DISTRICTS = {
    "Toshkent shahri": [
        "Bektemir", "Chilonzor", "Yashnobod", "Mirobod", "Mirzo Ulug'bek",
        "Sergeli", "Shayxontohur", "Olmazor", "Uchtepa", "Yakkasaroy",
        "Yunusobod", "Yangihayot",
    ],
    "Toshkent viloyati": [
        "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Qibray", "Ohangaron",
        "Oqqo'rg'on", "Parkent", "Piskent", "Quyi Chirchiq", "O'rta Chirchiq",
        "Yuqori Chirchiq", "Yangiyo'l", "Zangiota", "Nurafshon shahri",
        "Angren shahri", "Olmaliq shahri", "Chirchiq shahri",
    ],
    "Andijon": [
        "Andijon shahri", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi",
        "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat",
        "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor", "Xonobod",
    ],
    "Farg'ona": [
        "Farg'ona shahri", "Marg'ilon shahri", "Qo'qon shahri", "Beshariq",
        "Bog'dod", "Buvayda", "Dang'ara", "Furqat", "Quva", "Qushtepa",
        "Rishton", "So'x", "Toshloq", "Uchko'prik", "O'zbekiston", "Yozyovon",
    ],
    "Namangan": [
        "Namangan shahri", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq",
        "Namangan tumani", "Norin", "Pop", "To'raqo'rg'on", "Uychi",
        "Uchqo'rg'on", "Yangiqo'rg'on",
    ],
    "Samarqand": [
        "Samarqand shahri", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on",
        "Qo'shrabot", "Narpay", "Nurobod", "Oqdaryo", "Pastdarg'om",
        "Paxtachi", "Payariq", "Toyloq", "Urgut",
    ],
    "Buxoro": [
        "Buxoro shahri", "Kogon shahri", "Buxoro tumani", "G'ijduvon",
        "Jondor", "Vobkent", "Peshku", "Qorako'l", "Qorovulbozor",
        "Romitan", "Shofirkon", "Olot",
    ],
    "Xorazm": [
        "Urganch shahri", "Xiva", "Bog'ot", "Gurlan", "Hazorasp", "Xonqa",
        "Qo'shko'pir", "Shovot", "Urganch tumani", "Yangiariq", "Yangibozor",
    ],
    "Navoiy": [
        "Navoiy shahri", "Zarafshon shahri", "Konimex", "Karmana",
        "Qiziltepa", "Nurota", "Tomdi", "Uchquduq", "Xatirchi",
    ],
    "Qashqadaryo": [
        "Qarshi shahri", "Shahrisabz shahri", "Chiroqchi", "Dehqonobod",
        "G'uzor", "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak",
        "Nishon", "Qamashi", "Yakkabog'",
    ],
    "Surxondaryo": [
        "Termiz shahri", "Angor", "Boysun", "Denov", "Jarqo'rg'on",
        "Muzrabot", "Oltinsoy", "Qiziriq", "Qumqo'rg'on", "Sariosiyo",
        "Sherobod", "Sho'rchi", "Uzun",
    ],
    "Jizzax": [
        "Jizzax shahri", "Arnasoy", "Baxmal", "Do'stlik", "Forish",
        "G'allaorol", "Sharof Rashidov", "Yangiobod", "Zafarobod",
        "Zarbdor", "Zomin", "Mirzachul",
    ],
    "Sirdaryo": [
        "Guliston shahri", "Boyovut", "Guliston tumani", "Mirzaobod",
        "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos", "Yangiyer",
    ],
    "Qoraqalpog'iston": [
        "Nukus shahri", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
        "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanliko'l", "Qo'ng'irot",
        "Qorao'zak", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli",
    ],
}


# Har bir kun uchun standart soatlar oralig'i (vaqt boshqaruvida ishlatiladi)
DAY_HOURS = [f"{h:02d}:00" for h in range(8, 24)]  # 08:00 - 23:00
