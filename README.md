# 🎬 Telegram Mega Downloader Bot

Telegram'dagi **barcha** yopiq/cheklangan kontentni yuklab beruvchi shaxsiy bot.

## ✅ Nima yuklay oladi?

| Media turi | Qo'llab-quvvatlanadi |
|---|---|
| 🎬 Video | ✅ |
| 🖼 Rasm | ✅ |
| 📄 Har qanday fayl | ✅ |
| 🎵 Audio | ✅ |
| 🎤 Ovozli xabar | ✅ |
| ⭕ Video-xabar (round) | ✅ |
| 😊 Stiker | ✅ |
| 🎞 GIF | ✅ |
| 📖 Istoriya | ✅ |
| 📝 Matnli xabar | ✅ |

## 🚀 O'rnatish

### 1. API kalitlar — my.telegram.org

1. https://my.telegram.org ga kiring
2. "API development tools" bo'limi
3. Yangi ilova → **API_ID** va **API_HASH** oling

### 2. Bot — @BotFather

```
/newbot → nom → username → BOT_TOKEN oling
```

### 3. Session String (bir martalik, local kompyuterda)

```bash
pip install pyrogram tgcrypto
python get_session.py
```

Telefon raqam + SMS kod → **SESSION_STRING** chiqadi.

### 4. O'z User ID — @userinfobot

`/start` yuboring → **ALLOWED_USER_IDS** oling

### 5. GitHub'ga yuklash

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/SИЗNING/repo.git
git push -u origin main
```

### 6. Railway Deploy

1. https://railway.app → GitHub bilan login
2. **New Project → Deploy from GitHub repo**
3. Reponi tanlang
4. **Variables** bo'limiga qo'shing:

| Variable | Misol |
|---|---|
| `API_ID` | `12345678` |
| `API_HASH` | `abcdef1234abcdef` |
| `BOT_TOKEN` | `123456:ABCdef...` |
| `SESSION_STRING` | `BQA...` (uzun) |
| `ALLOWED_USER_IDS` | `123456789` yoki `123,456,789` |

5. **Deploy** ✅

## 📖 Foydalanish

```
https://t.me/c/3947294580/293        ← private kanal
https://t.me/publichkanal/100        ← public kanal
https://t.me/username/s/5            ← istoriya
```

Bir xabarda bir nechta havola — hammasi navbat bilan yuklanadi.

## ⚠️ Muhim

- SESSION_STRING = sizning Telegram hisobingiz. Hech kimga bermang.
- Bot faqat `ALLOWED_USER_IDS` da ko'rsatilgan odamlarga javob beradi.
- User-account ushbu kanalga a'zo bo'lishi kerak.
