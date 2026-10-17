# 🌍 TranslateBot Pro

Professional Telegram translation bot — 25+ tilda tarjima va so'z yodlash tizimi.

## 🚀 Xususiyatlar

| Xususiyat | Tavsif |
|-----------|--------|
| 🌐 **25+ Til** | 🇬🇧🇷🇺🇺🇿🇩🇪🇫🇷🇪🇸🇮🇹🇹🇷🇸🇦🇨🇳🇯🇵🇰🇷🇵🇹🇮🇳🇮🇷🇵🇱🇺🇦🇰🇿🇳🇱🇸🇪🇳🇴🇫🇮🇮🇱🇮🇩🇻🇳 |
| 🔍 **Auto-detect** | Til avtomatik aniqlanadi |
| 💾 **Lug'at** | So'zlarni saqlash, ko'rish, o'chirish |
| 🎯 **Quiz** | Spaced-repetition asosidagi test |
| 📊 **Statistika** | Natijalar va daraja tizimi |
| ⚙️ **Sozlamalar** | Manba/maqsad til tanlash |
| 🚀 **Tezlik** | In-process LRU cache — takroriy tarjima 0ms |

## 📁 Loyiha tuzilishi

```
translator_bot/
├── bot.py              ← Entry point, handler registration
├── config.py           ← Barcha sozlamalar, til ro'yxati
├── requirements.txt
├── .env.example        ← Token va env sozlamalari
│
├── database/
│   └── db.py           ← Async SQLite (aiosqlite), barcha DB operatsiyalar
│
├── handlers/
│   ├── start.py        ← /start, /help
│   ├── translate.py    ← Asosiy tarjima handleri
│   ├── vocabulary.py   ← Lug'at (list, save, delete)
│   ├── quiz.py         ← Quiz tizimi
│   ├── settings.py     ← Til sozlamalari
│   ├── stats.py        ← Statistika
│   ├── callbacks.py    ← Central inline callback router
│   └── menu.py         ← Reply keyboard menu router
│
├── services/
│   └── translator.py   ← deep_translator wrapper + LRU cache
│
└── keyboards/
    └── keyboards.py    ← Barcha InlineKeyboard va ReplyKeyboard builderlar
```

## ⚡ O'rnatish va ishga tushirish

### 1. Python muhitini sozlang

```bash
# Python 3.10+ kerak
python -m venv venv
venv\Scripts\activate          # Windows
# yoki: source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Token oling

1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Tokenni nusxalang

### 3. .env fayl yarating

```bash
copy .env.example .env
# .env faylini oching va BOT_TOKEN= ga tokeningizni qo'ying
```

### 4. Botni ishga tushiring

```bash
# Usul 1: .env orqali
python bot.py

# Usul 2: environment variable orqali
set BOT_TOKEN=1234567890:ABCdef...   # Windows
python bot.py
```

## 🎮 Foydalanish

```
Matn yozing  →  Darhol tarjima  →  💾 Lug'atga saqlash

/vocab        →  Saqlangan so'zlar ro'yxati (pagination bilan)
/quiz         →  4-variant test, natijalar saqlanadi
/stats        →  Daraja va aniqlik foizi
/settings     →  Til o'zgartirish (inline keyboard)
```

## 🌍 Qo'llab-quvvatlanadigan tillar (25 ta)

| Flag | Til | Kod |
|------|-----|-----|
| 🇬🇧 | English | `en` |
| 🇷🇺 | Русский | `ru` |
| 🇺🇿 | O'zbek | `uz` |
| 🇩🇪 | Deutsch | `de` |
| 🇫🇷 | Français | `fr` |
| 🇪🇸 | Español | `es` |
| 🇮🇹 | Italiano | `it` |
| 🇹🇷 | Türkçe | `tr` |
| 🇸🇦 | العربية | `ar` |
| 🇨🇳 | 中文 | `zh-cn` |
| 🇯🇵 | 日本語 | `ja` |
| 🇰🇷 | 한국어 | `ko` |
| 🇵🇹 | Português | `pt` |
| 🇮🇳 | हिन्दी | `hi` |
| 🇮🇷 | فارسی | `fa` |
| 🇵🇱 | Polski | `pl` |
| 🇺🇦 | Українська | `uk` |
| 🇰🇿 | Қазақша | `kk` |
| 🇳🇱 | Nederlands | `nl` |
| 🇸🇪 | Svenska | `sv` |
| 🇳🇴 | Norsk | `no` |
| 🇫🇮 | Suomi | `fi` |
| 🇮🇱 | עברית | `he` |
| 🇮🇩 | Bahasa Indonesia | `id` |
| 🇻🇳 | Tiếng Việt | `vi` |

## 🗄️ Ma'lumotlar bazasi

SQLite, 3 ta jadval:
- **users** — foydalanuvchi sozlamalari
- **vocabulary** — saqlangan so'zlar (spaced repetition ma'lumotlari bilan)
- **quiz_history** — har bir quiz urinishi

## 📈 Kelajakdagi xususiyatlar

- [ ] Webhook support (production uchun)
- [ ] Inline mode (`@bot so'z`)
- [ ] So'z talaffuzi (audio)
- [ ] Kunlik takrorlash eslatmasi
- [ ] Group chat support
- [ ] Import/Export lug'at (CSV)
