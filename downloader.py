import asyncio
import os
import re
import uuid
import glob
import time
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp
import yt_dlp
from config import DOWNLOAD_DIR, MAX_FILE_SIZE_BYTES

URL_REGEX = re.compile(
    r'(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'https?://[a-zA-Z0-9]+\.[^\s]{2,})'
)

# Qisqa muddatli URL kesh (token -> info)
MEDIA_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 1 soat

def clean_expired_cache():
    """Eskirgan kesh ma'lumotlarini tozalash."""
    now = time.time()
    expired = [k for k, v in MEDIA_CACHE.items() if now - v.get('time', 0) > CACHE_TTL]
    for k in expired:
        MEDIA_CACHE.pop(k, None)

def extract_urls(text: str) -> List[str]:
    """Matndan barcha havolalarni (URL) ajratib oladi."""
    return URL_REGEX.findall(text)

def normalize_url(url: str) -> str:
    """Havoladagi ortiqcha tracking parametrlarini tozalab, sof bazaviy havolani oladi."""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        netloc = parsed.netloc.lower()
        path = parsed.path

        # YouTube watch?v=
        if "youtube.com" in netloc and "/watch" in path:
            qs = urllib.parse.parse_qs(parsed.query)
            v = qs.get("v")
            if v:
                return f"https://www.youtube.com/watch?v={v[0]}"
        # YouTube shorts yoki youtu.be
        if "youtu.be" in netloc or "/shorts/" in path:
            clean_path = path.rstrip("/")
            return f"https://youtu.be{clean_path}" if "youtu.be" in netloc else f"https://www.youtube.com{clean_path}"
        # Instagram
        if "instagram.com" in netloc:
            clean_path = path.rstrip("/")
            return f"https://www.instagram.com{clean_path}/"
        # TikTok
        if "tiktok.com" in netloc:
            clean_path = path.rstrip("/")
            return f"https://www.tiktok.com{clean_path}"
        # Pinterest
        if "pinterest.com" in netloc or "pin.it" in netloc:
            clean_path = path.rstrip("/")
            return f"https://www.pinterest.com{clean_path}"
        # Twitter / X
        if "twitter.com" in netloc or "x.com" in netloc:
            clean_path = path.rstrip("/")
            return f"https://x.com{clean_path}"

        clean_url = f"{parsed.scheme}://{netloc}{path}".rstrip("/")
        return clean_url
    except Exception:
        return url.strip()

def identify_platform(url: str) -> str:
    """Havola qaysi platformaga tegishli ekanligini 0 soniyada aniqlaydi."""
    url_lower = url.lower()
    if "instagram.com" in url_lower:
        return "Instagram"
    elif "tiktok.com" in url_lower:
        return "TikTok"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "Pinterest"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter (X)"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "Facebook"
    elif "reddit.com" in url_lower:
        return "Reddit"
    elif "threads.net" in url_lower:
        return "Threads"
    elif "likee" in url_lower:
        return "Likee"
    elif "soundcloud.com" in url_lower:
        return "SoundCloud"
    elif "vk.com" in url_lower:
        return "VKontakte"
    return "Universal (Web)"

def create_instant_media_session(url: str) -> Dict[str, str]:
    """Havolani kutishlarsiz lahzada (0.01 sek) qabul qilib, sessiya yaratadi."""
    clean_expired_cache()
    platform = identify_platform(url)
    norm_url = normalize_url(url)
    token = str(uuid.uuid4())[:8]

    MEDIA_CACHE[token] = {
        'url': url,
        'normalized_url': norm_url,
        'platform': platform,
        'time': time.time()
    }

    return {
        'token': token,
        'platform': platform,
        'url': url,
        'normalized_url': norm_url
    }

async def download_pinterest_photo(url: str) -> Dict[str, Any]:
    """Pinterest rasmlarini asl sifatda yuklash."""
    headers = {
        'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'
    }
    unique_id = str(uuid.uuid4())[:8]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=45, connect=15)) as resp:
                if resp.status != 200:
                    return {'status': 'error', 'error': f"Pinterest sahifasiga ulanib bo'lmadi (Status: {resp.status})"}
                html = await resp.text()

        title_match = re.search(r'<title>([^<]+)</title>', html)
        title = title_match.group(1).replace(" | Pinterest", "").strip() if title_match else "Pinterest Media"

        og_image = re.search(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if not og_image:
            og_image = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']', html)

        if og_image and og_image.group(1):
            raw_img_url = og_image.group(1)
            original_img_url = re.sub(r'/\d+x/', '/originals/', raw_img_url)

            ext = ".png" if ".png" in raw_img_url.lower() else ".jpg"
            img_path = DOWNLOAD_DIR / f"{unique_id}_pinterest{ext}"

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(original_img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=aiohttp.ClientTimeout(total=30)) as img_resp:
                        if img_resp.status == 200:
                            content = await img_resp.read()
                            img_path.write_bytes(content)
                            return {
                                'status': 'success',
                                'is_photo': True,
                                'file_path': img_path,
                                'platform': 'Pinterest',
                                'title': title
                            }
                except Exception:
                    pass

                async with session.get(raw_img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=aiohttp.ClientTimeout(total=30)) as img_resp:
                    if img_resp.status == 200:
                        content = await img_resp.read()
                        img_path.write_bytes(content)
                        return {
                            'status': 'success',
                            'is_photo': True,
                            'file_path': img_path,
                            'platform': 'Pinterest',
                            'title': title
                        }

        return {'status': 'error', 'error': "Pinterest postidan rasm topilmadi."}
    except Exception as e:
        return {'status': 'error', 'error': f"Pinterest yuklashda xatolik: {e}"}

def _download_format_sync(url: str, quality: str, output_template: str) -> Dict[str, Any]:
    """Tezkor va xatosiz yuklab olish (uzoqroq timeout va avtomatik qayta urinishlar bilan)."""
    base_opts = {
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 60,              # Timeout xatosini oldini olish uchun 60 soniya
        'retries': 10,                     # 10 marta qayta urinish
        'fragment_retries': 10,
        'file_access_retries': 5,
        'extractor_retries': 5,
        'concurrent_fragment_downloads': 4,
    }

    if quality == "mp3":
        ydl_opts = {
            **base_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif quality == "best":
        ydl_opts = {
            **base_opts,
            'format': 'bestvideo[filesize<=48M]+bestaudio/best[filesize<=48M]/best',
            'merge_output_format': 'mp4',
            'max_filesize': MAX_FILE_SIZE_BYTES,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    else:
        h = int(quality)
        ydl_opts = {
            **base_opts,
            'format': f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return {'status': 'success', 'info': info, 'error': None}
        except yt_dlp.utils.DownloadError as e:
            err = str(e)
            if "No video formats found" in err:
                return {'status': 'no_video_formats', 'error': err}

            # Agar yuqori sifatda timeout yoki xatolik bo'lsa, 'best' bilan qayta urinish
            if quality not in ["best", "mp3"]:
                try:
                    fallback_opts = {
                        **base_opts,
                        'format': 'best',
                        'merge_output_format': 'mp4',
                    }
                    with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                        info = fallback_ydl.extract_info(url, download=True)
                        return {'status': 'success', 'info': info, 'error': None}
                except Exception as inner_e:
                    return {'status': 'error', 'error': str(inner_e)}
            return {'status': 'error', 'error': err}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

async def download_media_by_quality(token: str, quality: str) -> Dict[str, Any]:
    """Keshdagi token va tanlangan sifat bo'yicha to'g'ridan-to'g'ri tezkor yuklash."""
    cached = MEDIA_CACHE.get(token)
    if not cached:
        return {'status': 'error', 'error': "Havola eskirgan. Iltimos, havolani qaytadan yuboring."}

    url = cached['url']
    platform = cached['platform']

    unique_id = str(uuid.uuid4())[:8]
    ext_placeholder = "%(ext)s"
    output_template = str(DOWNLOAD_DIR / f"{unique_id}_media.{ext_placeholder}")

    # 1-urinish
    result = await asyncio.to_thread(_download_format_sync, url, quality, output_template)

    # Agar timeout bo'lsa, 1 marta avtomatik qayta urinish
    if result.get('status') == 'error' and 'timeout' in str(result.get('error', '')).lower():
        await asyncio.sleep(1)
        result = await asyncio.to_thread(_download_format_sync, url, quality, output_template)

    # Agar Pinterest postida video bo'lmasa, foto yuklash tizimiga yo'naltirish
    if result.get('status') == 'no_video_formats' or (result.get('status') != 'success' and platform == "Pinterest"):
        if platform == "Pinterest":
            return await download_pinterest_photo(url)

    if result['status'] != 'success':
        return result

    matched_files = glob.glob(str(DOWNLOAD_DIR / f"{unique_id}_media.*"))
    if not matched_files:
        if platform == "Pinterest":
            return await download_pinterest_photo(url)
        return {'status': 'error', 'error': "Yuklangan fayl diskda topilmadi."}

    file_path = Path(matched_files[0])
    file_size = file_path.stat().st_size

    if file_size > MAX_FILE_SIZE_BYTES:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        return {
            'status': 'file_too_large',
            'file_size_mb': round(file_size / (1024 * 1024), 1),
            'title': result.get('info', {}).get('title', 'Video'),
            'error': f"Fayl hajmi ({file_size / (1024 * 1024):.1f} MB) Telegram Bot limitidan (50 MB) katta."
        }

    info = result.get('info', {})
    title = info.get('title', 'Media fayl') if info else 'Media fayl'
    duration = info.get('duration', 0) if info else 0

    return {
        'status': 'success',
        'file_path': file_path,
        'platform': platform,
        'title': title,
        'duration': duration,
        'is_audio': (quality == "mp3")
    }
