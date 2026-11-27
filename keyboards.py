from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID, ADMIN_USERNAME, SUPPORT_CHAT_LINK

QUALITY_LABELS = {
    2160: "🎬 4K (2160p)",
    1440: "🎬 2K (1440p)",
    1080: "🎬 1080p (Full HD)",
    720:  "🎬 720p (HD)",
    480:  "🎬 480p",
    360:  "🎬 360p",
    240:  "🎬 240p",
    144:  "🎬 144p",
}

def get_platform_quality_keyboard(token: str, platform: str) -> InlineKeyboardMarkup:
    """Har bir platforma uchun mos tezkor sifat tanlash tugmalari."""
    if platform == "YouTube":
        keyboard = [
            [
                InlineKeyboardButton(text="🎬 1080p (Full HD)", callback_data=f"q:1080:{token}"),
                InlineKeyboardButton(text="🎬 720p (HD)", callback_data=f"q:720:{token}")
            ],
            [
                InlineKeyboardButton(text="🎬 480p", callback_data=f"q:480:{token}"),
                InlineKeyboardButton(text="🎬 360p", callback_data=f"q:360:{token}")
            ],
            [
                InlineKeyboardButton(text="🎬 4K (2160p)", callback_data=f"q:2160:{token}"),
                InlineKeyboardButton(text="🎬 2K (1440p)", callback_data=f"q:1440:{token}")
            ],
            [
                InlineKeyboardButton(text="🎬 240p", callback_data=f"q:240:{token}"),
                InlineKeyboardButton(text="🎬 144p", callback_data=f"q:144:{token}")
            ],
            [
                InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"q:mp3:{token}"),
                InlineKeyboardButton(text="⚡️ Eng yaxshi (Avto)", callback_data=f"q:best:{token}")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"q:cancel:{token}")
            ]
        ]
    elif platform in ["Instagram", "TikTok", "Likee", "Threads"]:
        keyboard = [
            [
                InlineKeyboardButton(text="🎬 Video (Eng yuqori sifat)", callback_data=f"q:best:{token}"),
                InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"q:mp3:{token}")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"q:cancel:{token}")
            ]
        ]
    elif platform == "Pinterest":
        keyboard = [
            [
                InlineKeyboardButton(text="🎬 / 🖼 Yuklab olish (Asl sifat)", callback_data=f"q:best:{token}"),
                InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"q:mp3:{token}")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"q:cancel:{token}")
            ]
        ]
    else:  # Facebook, Twitter/X, Reddit, Universal
        keyboard = [
            [
                InlineKeyboardButton(text="🎬 1080p (Full HD)", callback_data=f"q:1080:{token}"),
                InlineKeyboardButton(text="🎬 720p (HD)", callback_data=f"q:720:{token}")
            ],
            [
                InlineKeyboardButton(text="🎬 480p", callback_data=f"q:480:{token}"),
                InlineKeyboardButton(text="🎬 360p", callback_data=f"q:360:{token}")
            ],
            [
                InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data=f"q:mp3:{token}"),
                InlineKeyboardButton(text="⚡️ Eng yaxshi (Avto)", callback_data=f"q:best:{token}")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"q:cancel:{token}")
            ]
        ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Foydalanuvchi asosiy menyu klaviaturasi."""
    buttons = [
        [KeyboardButton(text="💬 Admin bilan aloqa / Muhokama"), KeyboardButton(text="ℹ️ Bot haqida")],
        [KeyboardButton(text="💡 Qo'llanma")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True
    )

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel inline klaviaturasi."""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Xabar tarqatish (Broadcast)", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="💬 Admin kontakti", callback_data="admin_contact_info")
        ],
        [
            InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Xabar tarqatishni tasdiqlash tugmalari."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_contact_inline_keyboard() -> InlineKeyboardMarkup:
    """Admin bilan to'g'ridan-to'g'ri bog'lanish yoki muhokama tugmasi."""
    keyboard = []
    if SUPPORT_CHAT_LINK and SUPPORT_CHAT_LINK.startswith("http"):
        keyboard.append([InlineKeyboardButton(text="💬 Muhokama guruhi / Kanal", url=SUPPORT_CHAT_LINK)])
    
    if ADMIN_USERNAME:
        clean_user = ADMIN_USERNAME.replace("@", "")
        keyboard.append([InlineKeyboardButton(text="👤 Admin bilan yozishish", url=f"https://t.me/{clean_user}")])
    else:
        keyboard.append([InlineKeyboardButton(text="👤 Admin profili", url=f"tg://user?id={ADMIN_ID}")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
