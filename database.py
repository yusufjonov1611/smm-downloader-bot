import aiosqlite
from datetime import datetime
from config import DB_PATH

async def init_db():
    """Ma'lumotlar bazasini initsializatsiya qilish."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_downloads INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                url TEXT,
                title TEXT,
                status TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Telegram File ID Kesh jadvali: bir marta yuklangan fayllar shu yerda saqlanadi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS media_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_url TEXT,
                quality TEXT,
                file_id TEXT,
                file_type TEXT,
                title TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_media_cache ON media_cache(normalized_url, quality)
        """)
        await db.commit()

async def add_or_update_user(user_id: int, username: str | None, full_name: str):
    """Foydalanuvchini bazaga qo'shish yoki faolligini yangilash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name, last_active)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = CURRENT_TIMESTAMP
        """, (user_id, username or "", full_name))
        await db.commit()

async def increment_user_downloads(user_id: int):
    """Foydalanuvchining yuklab olishlar hisoblagichini oshirish."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET total_downloads = total_downloads + 1 WHERE user_id = ?
        """, (user_id,))
        await db.commit()

async def log_download(user_id: int, platform: str, url: str, title: str, status: str = "success"):
    """Yuklangan fayl haqida ma'lumotni saqlash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO downloads (user_id, platform, url, title, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, platform, url, title, status))
        await db.commit()
    await increment_user_downloads(user_id)

async def get_cached_media(normalized_url: str, quality: str):
    """Keshdan Telegram file_id sini qidirish."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id, file_type, title FROM media_cache WHERE normalized_url = ? AND quality = ? ORDER BY id DESC LIMIT 1",
            (normalized_url, quality)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'file_id': row[0],
                    'file_type': row[1],
                    'title': row[2]
                }
    return None

async def save_cached_media(normalized_url: str, quality: str, file_id: str, file_type: str, title: str):
    """Faylning Telegram file_id sini keshga saqlash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO media_cache (normalized_url, quality, file_id, file_type, title)
            VALUES (?, ?, ?, ?, ?)
        """, (normalized_url, quality, file_id, file_type, title))
        await db.commit()

async def get_statistics():
    """Bot statistikasi: foydalanuvchilar, yuklashlar va kesh soni."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')") as cursor:
            today_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM downloads WHERE status = 'success'") as cursor:
            total_downloads = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM downloads WHERE status = 'success' AND DATE(downloaded_at) = DATE('now')") as cursor:
            today_downloads = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM media_cache") as cursor:
            cached_files = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "today_users": today_users,
        "total_downloads": total_downloads,
        "today_downloads": today_downloads,
        "cached_files": cached_files
    }

async def get_all_user_ids():
    """Barcha faol foydalanuvchilar IDlarini olish (Broadcast uchun)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
