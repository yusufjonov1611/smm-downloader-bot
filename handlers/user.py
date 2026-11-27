import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import add_or_update_user, log_download, get_cached_media, save_cached_media
from downloader import (
    extract_urls,
    create_instant_media_session,
    download_media_by_quality,
    normalize_url,
    MEDIA_CACHE
)
from keyboards import (
    get_main_keyboard,
    get_contact_inline_keyboard,
    get_platform_quality_keyboard,
    QUALITY_LABELS
)

user_router = Router()

def format_duration(seconds: int) -> str:
    """Soniyalarni mm:ss yoki hh:mm:ss formatga o'tkazish."""
    if not seconds:
        return "Noma'lum"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi."""
    await state.clear()
    user = message.from_user
    is_admin = (user.id == ADMIN_ID)

    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>! 👋\n\n"
        "Men <b>SMM Downloader Bot</b>man 🚀\n\n"
        "Menga istalgan ijtimoiy tarmoqdan (Instagram, TikTok, YouTube, Pinterest, "
        "Twitter/X, Facebook, Reddit va boshqalar) havola yuboring.\n\n"
        "⚡️ <b>Aqlli Kesh Tizimi:</b> Botga bir marta yuklangan har qanday video yoki musiqa "
        "bazada saqlanadi va keyingi safar qaytadan yuklab o'tirmasdan <b>0.1 soniyada</b> yetkaziladi!\n\n"
        "📥 <i>Shunchaki video havolasini shu yerga yuboring...</i>"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )

@user_router.message(Command("help"))
@user_router.message(F.text == "💡 Qo'llanma")
async def cmd_help(message: Message):
    """Qo'llanma va yordam."""
    help_text = (
        "📖 <b>Botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "1. Video yoki post havolasini nusxalang.\n"
        "2. Havolani botga yuboring.\n"
        "3. Kerakli sifat yoki formatni tanlang:\n"
        "   • <b>4K (2160p) & 2K (1440p)</b> — Ultra sifat\n"
        "   • <b>1080p & 720p</b> — Yuqori HD sifat\n"
        "   • <b>480p, 360p, 240p, 144p</b> — Trafikni tejovchi formatlar\n"
        "   • <b>🎵 Audio (MP3)</b> — Faqat musiqasini yuklab olish\n"
        "4. Bot faylni yuklab sizga yetkazadi.\n\n"
        "⚡️ <i>Agar bu video avval kimdir tomonidan yuklangan bo'lsa, sizga kutishlarsiz lahzada yuboriladi!</i>"
    )
    await message.answer(help_text, parse_mode="HTML")

@user_router.message(Command("contact"))
@user_router.message(F.text == "💬 Admin bilan aloqa / Muhokama")
async def cmd_contact(message: Message, state: FSMContext):
    """Admin bilan aloqa va muhokama."""
    await state.clear()
    text = (
        "💬 <b>Muhokama va Aloqa bo'limi:</b>\n\n"
        "Savol, taklif yoki fikr-mulohazalaringiz bo'lsa, adminga murojaat qilishingiz mumkin:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_contact_inline_keyboard())

@user_router.message(F.text == "ℹ️ Bot haqida")
async def cmd_about(message: Message):
    """Bot haqida ma'lumot."""
    about_text = (
        "🤖 <b>SMM Downloader Bot</b>\n\n"
        "Ijtimoiy tarmoqlardan video va audio fayllarni turli sifatlarda (144p dan 4K gacha) "
        "va MP3 formatida juda tez yuklab beruvchi universal bot.\n\n"
        "⚡️ Tezkor kesh tizimi bilan jihozlangan!"
    )
    await message.answer(about_text, parse_mode="HTML")

@user_router.callback_query(F.data.startswith("q:"))
async def handle_quality_choice(callback: CallbackQuery, bot: Bot):
    """Foydalanuvchi video sifatini tanlaganda ishga tushadi."""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    _, quality_code, token = parts

    # Bekor qilish
    if quality_code == "cancel":
        await callback.message.delete()
        await callback.answer("Yuklash bekor qilindi.")
        return

    # Sifat nomi
    if quality_code == "mp3":
        quality_label = "🎵 Audio (MP3)"
    elif quality_code == "best":
        quality_label = "⚡️ Eng yaxshi sifat"
    else:
        quality_label = QUALITY_LABELS.get(int(quality_code), f"🎬 {quality_code}p")

    cached_session = MEDIA_CACHE.get(token)
    norm_url = cached_session.get('normalized_url') if cached_session else None
    platform = cached_session.get('platform', 'Internet') if cached_session else 'Internet'
    raw_url = cached_session.get('url', '') if cached_session else ''

    # ==========================================
    # ⚡️ 1. TELEGRAM KESHIDAN TEKSHIRISH (0.1 SEKUNDDA YUBORISH)
    # ==========================================
    if norm_url:
        cached_media = await get_cached_media(norm_url, quality_code)
        if cached_media:
            await callback.answer(f"{quality_label} (Keshdan) ⚡️")
            bot_info = await bot.get_me()
            title = cached_media['title']
            file_id = cached_media['file_id']
            file_type = cached_media['file_type']

            caption = (
                f"🎬 <b>{title[:100]}</b>\n\n"
                f"📊 Format: <b>{quality_label}</b> (⚡️ Keshdan darhol)\n"
                f"🌐 Manba: <b>{platform}</b>\n"
                f"🤖 @{bot_info.username}"
            )

            try:
                if file_type == 'audio':
                    await callback.message.answer_audio(audio=file_id, caption=caption, parse_mode="HTML")
                elif file_type == 'photo':
                    await callback.message.answer_photo(photo=file_id, caption=caption, parse_mode="HTML")
                else:
                    await callback.message.answer_video(video=file_id, caption=caption, parse_mode="HTML", supports_streaming=True)

                await log_download(callback.from_user.id, platform, raw_url, title, "cached_hit")
                await callback.message.delete()
                return
            except Exception:
                # Agar Telegram keshidagi fayl ID eskirgan bo'lsa, pastga o'tib qayta yuklaydi
                pass

    # ==========================================
    # 2. AGAR KESHDA BO'LMASA -> YUKLAB OLISH
    # ==========================================
    await callback.answer(f"{quality_label} tanlandi")

    await callback.message.edit_text(
        f"⏳ <b>[{quality_label}]</b> formatda yuklanmoqda...\n"
        "<i>Iltimos kuting, fayl tayyorlanmoqda...</i>",
        parse_mode="HTML"
    )

    try:
        result = await download_media_by_quality(token, quality_code)

        if result['status'] == 'file_too_large':
            file_size_mb = result.get('file_size_mb', 50)
            await callback.message.edit_text(
                f"⚠️ <b>Kechirasiz!</b>\n\n"
                f"Tanlangan <b>[{quality_label}]</b> formatdagi fayl hajmi (<b>{file_size_mb} MB</b>) "
                "Telegram bot limiti (50 MB) dan oshib ketdi.\n\n"
                "👇 <i>Iltimos, pastroq sifatni (masalan 720p yoki 480p) tanlang yoki MP3 formatda yuklang:</i>",
                parse_mode="HTML",
                reply_markup=get_platform_quality_keyboard(token, platform)
            )
            return

        if result['status'] != 'success':
            err_msg = result.get('error', "Yuklab olishda xatolik yuz berdi.")
            if "timeout" in err_msg.lower():
                err_msg = "Tarmoq ulanishida vaqtinchalik uzilish bo'ldi. Iltimos, qaytadan urinib ko'ring yoki boshqa sifatni tanlang."
            await callback.message.edit_text(
                f"❌ <b>Xatolik yuz berdi:</b>\n\n<i>{err_msg}</i>",
                parse_mode="HTML",
                reply_markup=get_platform_quality_keyboard(token, platform)
            )
            return

        file_path = result['file_path']
        title = result.get('title', 'Media fayl')
        is_audio = result.get('is_audio', False)
        is_photo = result.get('is_photo', False)

        bot_info = await bot.get_me()
        caption = (
            f"🎬 <b>{title[:100]}</b>\n\n"
            f"📊 Format: <b>{quality_label}</b>\n"
            f"🌐 Manba: <b>{platform}</b>\n"
            f"🤖 @{bot_info.username}"
        )

        input_file = FSInputFile(str(file_path))

        sent_msg = None
        saved_file_id = None
        saved_file_type = None

        if is_photo:
            sent_msg = await callback.message.answer_photo(
                photo=input_file,
                caption=caption,
                parse_mode="HTML"
            )
            if sent_msg and sent_msg.photo:
                saved_file_id = sent_msg.photo[-1].file_id
                saved_file_type = 'photo'
        elif is_audio:
            sent_msg = await callback.message.answer_audio(
                audio=input_file,
                caption=caption,
                title=title[:60],
                parse_mode="HTML"
            )
            if sent_msg and sent_msg.audio:
                saved_file_id = sent_msg.audio.file_id
                saved_file_type = 'audio'
        else:
            sent_msg = await callback.message.answer_video(
                video=input_file,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True
            )
            if sent_msg and sent_msg.video:
                saved_file_id = sent_msg.video.file_id
                saved_file_type = 'video'

        # ⚡️ TELEGRAM FILE_ID NI KESH BAZASIGA SAQLASH
        if saved_file_id and norm_url:
            await save_cached_media(norm_url, quality_code, saved_file_id, saved_file_type, title)

        # Log yozish
        await log_download(
            user_id=callback.from_user.id,
            platform=platform,
            url=raw_url,
            title=title,
            status="success"
        )

        # Status xabarni tozalash
        await callback.message.delete()

    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Xatolik:</b>\n{str(e)[:300]}",
            parse_mode="HTML"
        )
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

@user_router.message(F.text)
async def handle_incoming_text(message: Message):
    """Foydalanuvchi havola yuborishi bilan LAHZADA sifat tanlash tugmalarini chiqarish."""
    urls = extract_urls(message.text or "")
    if not urls:
        await message.reply(
            "Iltimos, video yoki kontent yuklab olish uchun to'g'ri havola (link) yuboring. 📥\n"
            "Yordam uchun: /help",
            parse_mode="HTML"
        )
        return

    url = urls[0]
    session = create_instant_media_session(url)
    token = session['token']
    platform = session['platform']

    short_url = url if len(url) <= 50 else url[:47] + "..."

    prompt_text = (
        f"🌐 Manba: <b>{platform}</b>\n"
        f"🔗 Havola: <code>{short_url}</code>\n\n"
        f"👇 <b>Kerakli video sifatini yoki formatni tanlang:</b>"
    )

    await message.reply(
        prompt_text,
        parse_mode="HTML",
        reply_markup=get_platform_quality_keyboard(token, platform)
    )
