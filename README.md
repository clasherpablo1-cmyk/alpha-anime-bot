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
