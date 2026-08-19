# Obuna Tanga Boti

Instagram obunachi almashish uchun Telegram bot + tanga tizimi.

## Qanday ishlaydi

1. Foydalanuvchi "🎯 Vazifa bajarish" tugmasini bosadi — botdan kimningdir
   Instagram sahifasi havolasini oladi.
2. O'sha sahifaga obuna bo'ladi va screenshot yuboradi.
3. Screenshot adminga (sizga) yuboriladi — siz "✅ Tasdiqlash" yoki
   "❌ Rad etish" tugmasini bosasiz.
4. Tasdiqlansa, foydalanuvchiga tanga qo'shiladi.
5. Foydalanuvchi "📢 Post qilish" orqali o'z Instagram sahifasini vazifa
   qilib qo'yadi (buning uchun tanga sarflanadi) — boshqalar unga obuna
   bo'lib beradi.

## O'rnatish

### 1. Telegram bot yarating

Telegram'da @BotFather ga yozing, `/newbot` buyrug'ini yuboring,
bot nomini tanlang. Sizga token beriladi (masalan
`123456:ABC-DEF1234...`) — shuni saqlab qo'ying.

### 2. O'z Telegram ID raqamingizni bilib oling

@userinfobot ga yozing — u sizga ID raqamingizni ko'rsatadi.

### 3. Loyihani sozlang

Terminalda loyiha papkasida:

```
python -m venv venv
```

Windows:
```
.\venv\Scripts\activate
```
Mac/Linux:
```
source venv/bin/activate
```

Keyin:
```
pip install -r requirements.txt
```

### 4. .env faylini sozlang

`.env.example` faylidan nusxa oling va nomini `.env` ga o'zgartiring.
Ichiga:
- `BOT_TOKEN` — BotFather'dan olgan tokeningiz
- `ADMIN_IDS` — sizning Telegram ID raqamingiz
- `COIN_PER_FOLLOW` — bitta obuna uchun necha tanga berilishi (standart: 10)

### 5. Botni ishga tushiring

```
python bot.py
```

Terminalda "Bot ishga tushdi..." degan yozuv chiqsa — bot ishlayapti.
Telegram'da botingizga o'ting va `/start` bosing.

## Muhim eslatmalar

- Bu bot **haqiqiy odamlar orasida almashinuv** qiladi — ya'ni
  foydalanuvchilar bir-birlarining sahifasiga real obuna bo'lishadi.
  Bot hech kimni avtomatik obuna qildirmaydi va soxta akkount yaratmaydi.
- Screenshotlarni diqqat bilan tekshiring — soxta yoki eski
  screenshotlar yuborilishi mumkin.
- Ma'lumotlar `obuna_bot.db` faylida (SQLite) saqlanadi. Bu faylni
  zaxira nusxalashni unutmang.
- Botni doimiy ishlashi uchun (kompyuteringiz o'chganda ham) uni
  serverga (VPS) joylashtirish kerak bo'ladi — buni alohida so'rasangiz
  yordam beraman.

## Fayllar tuzilishi

```
obuna-bot/
  bot.py          - botning asosiy logikasi
  database.py     - SQLite bilan ishlash funksiyalari
  requirements.txt
  .env.example    - sozlamalar namunasi (.env qilib nusxalang)
  README.md
```
