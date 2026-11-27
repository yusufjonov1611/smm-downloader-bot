# SMM Downloader Bot (@smm_downbot)

Universal ijtimoiy tarmoqlar va 1000+ veb-saytlardan media (video, rasm, audio) yuklab beruvchi professional Telegram bot.

## 🚀 Imkoniyatlar:
- **Universal yuklovchi:** Instagram (Reels, Post, Karusel), TikTok (suv belgisisiz), YouTube (Shorts, Video, Audio), Pinterest, Twitter (X), Facebook, Reddit, Threads, Likee, SoundCloud va boshqa 1000+ saytlar.
- **Admin Panel:**
  - 📊 Real vaqt statistikasi (jami foydalanuvchilar, bugun qo'shilganlar, yuklashlar soni).
  - 📢 Barcha foydalanuvchilarga xabar tarqatish (Broadcast - matn, rasm, video va h.k.).
  - 💬 Admin kontakti va muhokama bo'limi boshqaruvi.
- **Avtomatik tozalash:** Yuklangan fayllar foydalanuvchiga yuborilgach, disk maydonini tejash uchun serverdan avtomatik o'chiriladi.
- **Telegram komandalar:** `/start`, `/help`, `/contact` va admin uchun maxsus `/admin` komandasi.

## 📁 Loyiha tarkibi:
- `main.py` — Botning asosiy kirish nuqtasi va komandalar sozlamasi
- `downloader.py` — `yt-dlp` va `ffmpeg` asosidagi universal yuklovchi
- `database.py` — SQLite asinxron ma'lumotlar bazasi
- `keyboards.py` — Qulay Reply va Inline klaviaturalar
- `handlers/` — Foydalanuvchi va admin xabarlari bilan ishlovchi modullar
- `.env` — Bot tokeni, Admin ID va kontaktlar
- `run_bot.bat` — Windows tizimida botni 1 klik bilan ishga tushirish fayli

## ⚙️ Ishga tushirish:
1. Loyiha papkasida `run_bot.bat` faylini ikki marta bosing.
   Yoki buyruqlar satrida:
   ```cmd
   .venv\Scripts\python.exe main.py
   ```
