# 🎌 «Uzbekcha animelar» Telegram Bot va Kanal Ekotizimi

Ushbu loyiha **@Alpha_animelar_bot** boti va **@uzbekcha_animelar_alpha** Telegram kanali uchun maxsus ishlab chiqilgan, yuqori tezlikdagi to'liq asinxron (Production-Ready) ekotizimdir.

---

## 🚀 Asosiy Imkoniyatlar

1. **🔢 Kod bo'yicha qidiruv & Yuklab berish:**
   - Foydalanuvchi anime kodini (masalan: `1`, `105` yoki `#kod_1`) yozsa, bot animening to'liq ma'lumotlarini (poster, janrlar, qismlar) chiqarib beradi.
   - Qism tugmasini bosganda video faylni darhol yuboradi.
2. **📢 Majburiy a'zolik (Forced Subscription Guard):**
   - Botdan foydalanish uchun foydalanuvchilar `@uzbekcha_animelar_alpha` kanaliga a'zo bo'lishi shart.
   - Obuna bo'lmaganlarga a'zo bo'lish va «✅ Obunani tekshirish» tugmalari ko'rsatiladi.
3. **🌐 AniList API Integratsiyasi (Avtomatik to'ldirish):**
   - Admin yangi anime nomini kiritganda, bot xalqaro AniList bazasidan animening rasmiy nomi, yili, janrlari, studiyasi, qismlar soni va HD posterini avtomatik topib beradi.
4. **📢 Bitta bosish bilan kanalga post chiqarish:**
   - Admin bot ichida tayyorlangan anime kartochkasini to'g'ridan-to'g'ri kanalga poster, ma'lumotlar va botga yo'naltiruvchi maxsus tugma (`t.me/Alpha_animelar_bot?start=KOD`) bilan chiqarishi mumkin.
5. **☁️ Telegram Cloud Storage (0 MB Server xarajati):**
   - Yuklangan barcha videofayllar Telegram serverlarida bepul saqlanadi (`file_id`). Server xotirasi to'lmaydi.
6. **✉️ Xabar tarqatish (Broadcast):**
   - Barcha bot a'zolariga yangilik yoki reklama yuborish.
7. **📊 Jonli Statistika:**
   - Foydalanuvchilar, animelar, qismlar, ko'rishlar va yuklab olishlar soni.

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Talablar:
- Python 3.11 yoki undan yuqori (Hozirgi tizimda: Python 3.14 o'rnatilgan)

### 2. Kutubxonalarni o'rnatish:
```powershell
pip install -r requirements.txt
```

### 3. Botni ishga tushirish:
- Windows'da tayyor `start_bot.bat` fayliga 2 marta bosing, yoki konsoldan quyidagini ishga tushiring:
```powershell
python bot.py
```

---

## 👑 Admin Huquqini Olish

Bot ishga tushgach, o'zingizning Telegram akkauntingizdan `@Alpha_animelar_bot` ga kiring va quyidagi buyruqni yuboring:

```text
/claim_admin anime2026
```

Shundan so'ng sizga darhol **Admin huquqi** beriladi va bot menyusida **«⚙️ Admin Panel»** paydo bo'ladi!

---

## 📖 Admin Boshqaruvi Bo'yicha Qo'llanma

### 🎬 Yangi anime qo'shish:
1. Admin panelda **«➕ Yangi anime qo'shish»** tugmasini bosing.
2. Animening nomini inglizcha yoki yaponcha yozing (masalan: *Naruto*, *Solo Leveling*, *Attack on Titan*).
3. Bot AniList'dan barcha ma'lumotlarni topadi. O'zbekcha nomini tasdiqlang va kod bering (masalan: `1`).

### 🎞 Qismlarni yuklash:
1. **«🎬 Qism yuklash»** tugmasini bosing.
2. Anime kodini va qism raqamini kiriting (masalan: 1-qism).
3. Videoni Telegram orqali yuboring. Bo'ldi, qism saqlandi!

### 📢 Kanalga post chiqarish:
1. **«📢 Kanalga post chiqarish»** tugmasini bosing va anime kodini kiriting (yoki anime kartochkasidagi tugmani bosing).
2. Chiqqan previewni ko'zdan kechirib, **«✅ Ha, kanalga chiqarilsin»** tugmasini bosing.
3. Post darhol `@uzbekcha_animelar_alpha` kanaliga chiroyli dizaynda chiqadi!

---

## 🌐 24/7 BULUTLI HOSTING VA VEB-SERVER (CLOUD DEPLOYMENT)

Bot internetda kompyuteringiz o'chiq paytida ham **24/7 to'xtovsiz, bepul va avtomatik** ishlashi uchun to'liq moslashtirilgan:

### 1. Jonli Veb-Server va Health Check:
Bot ishga tushishi bilan bir vaqtda fon rejimida zamonaviy `aiohttp.web` serveri faollashadi:
- **`http://localhost:8080/`** — Tizimning jonli HTML dashboardi (Uptime, animelar, qismlar, ko'rishlar).
- **`http://localhost:8080/health`** — JSON formatidagi sog'lomlik tekshiruvi (`HTTP 200 OK`).
- **`http://localhost:8080/ping`** — O'ta yengil ping javobi (`{"status": "pong"}`).

### 2. Render.com orqali 24/7 bepul ishga tushirish (1-klik):
1. **[render.com](https://render.com)** saytiga kiring va GitHub akkauntingiz (`clasherpablo`) bilan kiring.
2. **New +** -> **Web Service** ni tanlang va ushbu repozitoriyni ulang.
3. Sozlamalar:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Health Check Path:** `/health`
4. **Environment Variables** bo'limiga `.env` dagi qiymatlarni kiriting:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `ADMIN_SECRET_KEY`
   - `CHANNEL_USERNAME`
   - `CHANNEL_URL`
   - `PORT` = `10000` (Render standarti)
5. **Deploy Web Service** ni bosing! Render botni darhol internetda ishga tushiradi.

### 3. UptimeRobot orqali 24/7 "Uxlab Qolmaslik" (Keep-Alive):
Render bepul tarifida veb-servislar 15 daqiqa so'rov bo'lmasa uyquga ketadi. Buni 100% bartaraf etish uchun:
1. **[uptimerobot.com](https://uptimerobot.com)** saytiga bepul ro'yxatdan o'ting.
2. **Add New Monitor** tugmasini bosing:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Alpha Anime Bot`
   - **URL (or IP):** `https://sizning-render-manzilingiz.onrender.com/health`
   - **Monitoring Interval:** `Every 5 minutes`
3. **Create Monitor** ni bosing! Endi UptimeRobot har 5 daqiqada botingizga so'rov yuboradi va bot **yil bo'yi 24/7 uzluksiz** ishlaydi!

---

## 🛡 Lokal 24/7 Nazoratchi (Self-Healing Watchdog)
Agar botni o'z kompyuteringizda yoki shaxsiy VPS serveringizda 24/7 ishlatmoqchi bo'lsangiz:
- `run_24_7.bat` fayliga 2 marta bosing (yoki konsolda `python run_24_7.py`).
- Ushbu skript botni uzluksiz kuzatib boradi va internet uzilsa yoki xatolik bo'lsa, uni **avtomatik soniyalar ichida qayta tiriltiradi**.
