import os
import time
import asyncio
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from config import DOWNLOAD_DIR, PROGRESS_UPDATE_EVERY, BROWSER_COOKIES
from utils.progress import fmt_size, fmt_speed

logger = logging.getLogger(__name__)
_YTDLP_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ytdlp")

PLATFORM_NAMES = {
    "youtube.com":     "▶️ YouTube",
    "youtu.be":        "▶️ YouTube",
    "instagram.com":   "📸 Instagram",
    "tiktok.com":      "🎵 TikTok",
    "twitter.com":     "🐦 Twitter/X",
    "x.com":           "🐦 Twitter/X",
    "facebook.com":    "👤 Facebook",
    "vimeo.com":       "🎬 Vimeo",
    "reddit.com":      "👾 Reddit",
    "twitch.tv":       "🎮 Twitch",
    "ok.ru":           "🌐 OK.ru",
    "vk.com":          "🌐 VK",
    "dailymotion.com": "🎬 Dailymotion",
}


def detect_platform(url: str) -> str:
    for domain, name in PLATFORM_NAMES.items():
        if domain in url:
            return name
    return "🌐 Video"


def is_external_link(url: str) -> bool:
    normalized = (url or "").lower()
    return any(d in normalized for d in PLATFORM_NAMES)


def _make_cookie_file(env_key: str, prefix: str):
    content = os.environ.get(env_key, "").strip()
    if not content:
        return None
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix=prefix
    )
    if not content.startswith("# Netscape"):
        tmp.write("# Netscape HTTP Cookie File\n")
    tmp.write(content)
    tmp.close()
    return tmp.name


def _cleanup(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def make_progress_hook(status_msg, loop, label: str):
    last_update = [0.0]

    def hook(d):
        now = time.time()
        if now - last_update[0] < PROGRESS_UPDATE_EVERY:
            return
        last_update[0] = now

        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total      = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed      = d.get("speed", 0) or 0
            eta        = d.get("eta", 0) or 0

            if total:
                pct = downloaded / total * 100
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                text = (
                    f"{label}\n\n"
                    f"{bar} {pct:.1f}%\n"
                    f"📦 {fmt_size(downloaded)} / {fmt_size(total)}\n"
                    f"⚡ {fmt_speed(speed)}\n"
                    f"⏱ {int(eta)}s qoldi"
                )
            else:
                text = f"{label}\n📦 {fmt_size(downloaded)} yuklanmoqda..."

            asyncio.run_coroutine_threadsafe(_safe_edit(status_msg, text), loop)

    return hook


async def _safe_edit(msg, text: str):
    try:
        await msg.edit(text)
    except Exception:
        pass


async def download_external(url: str, status_msg, quality: str = "best") -> tuple:
    url = (url or "").strip()
    platform = detect_platform(url)
    await status_msg.edit(f"{platform} yuklanmoqda...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_tmpl = os.path.join(DOWNLOAD_DIR, "%(title).50s.%(ext)s")
    loop = asyncio.get_event_loop()
    hook = make_progress_hook(status_msg, loop, f"{platform} yuklanmoqda...")

    # Cookie fayllar
    yt_cookie  = _make_cookie_file("YOUTUBE_COOKIES",   "yt_")
    ig_cookie  = _make_cookie_file("INSTAGRAM_COOKIES", "ig_")

    ydl_opts = {
        "outtmpl":        output_tmpl,
        "progress_hooks": [hook],
        "quiet":          True,
        "no_warnings":    True,
        "noplaylist":     True,
        "socket_timeout": 30,
        "retries":        3,
        # ffmpeg siz ishlaydigan tayyor mp4 format
        "format":         "best[ext=mp4]/best",
    }

    # Sifat tanlash
    if quality == "audio":
        ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio"
    elif quality == "720":
        ydl_opts["format"] = "best[height<=720][ext=mp4]/best[height<=720]"
    elif quality == "480":
        ydl_opts["format"] = "best[height<=480][ext=mp4]/best[height<=480]"

    # Cookie qo'shish
    if "instagram.com" in url and ig_cookie:
        ydl_opts["cookiefile"] = ig_cookie
    elif yt_cookie:
        ydl_opts["cookiefile"] = yt_cookie
    elif BROWSER_COOKIES:
        ydl_opts["cookiesfrombrowser"] = (BROWSER_COOKIES,)

    try:
        file_path = await loop.run_in_executor(
            _YTDLP_EXECUTOR, lambda: _run_download(ydl_opts, url)
        )
        mtype = "audio" if quality == "audio" else "video"
        return file_path, mtype

    except yt_dlp.utils.DownloadError as e:
        err = str(e)
        low = err.lower()
        if "Private" in err:
            raise Exception("Bu video yopiq (private).")
        if "unavailable" in low:
            raise Exception("Video mavjud emas yoki o'chirilgan.")
        if "sign in to confirm" in low or "cookies" in low:
            raise Exception(
                "YouTube kontenti uchun autentifikatsiya kerak. "
                "Railway env ga YOUTUBE_COOKIES (Netscape format) qo'shing."
            )
        raise Exception(err[:300])

    finally:
        _cleanup(yt_cookie, ig_cookie)


def _run_download(opts: dict, url: str) -> str:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        for ext in (".webm", ".mkv"):
            if path.endswith(ext):
                path = path.replace(ext, ".mp4")
        return path
