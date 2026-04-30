import os
import time
import logging
from functools import partial

from pyrogram import Client
from pyrogram.types import Message as PyroMsg

from config import DOWNLOAD_DIR, MAX_BOT_SIZE_MB, MEDIA_LABELS
from utils.audio_optimizer import compress_audio_file
from utils.progress import progress_callback, fmt_size

logger = logging.getLogger(__name__)


def get_media_and_type(msg):
    for attr in ("video", "photo", "document", "audio",
                 "voice", "video_note", "sticker", "animation"):
        media = getattr(msg, attr, None)
        if media:
            return media, attr
    return None, None


async def download_message(user: Client, peer, msg_id: int, status_msg) -> tuple:
    msg = await user.get_messages(peer, msg_id)
    if not msg or msg.empty:
        return None, "empty"
    media, mtype = get_media_and_type(msg)
    if not media:
        return msg.text or msg.caption or "", "text"
    file_size = getattr(media, "file_size", 0) or 0
    nice_label = MEDIA_LABELS.get(mtype, "📁 Fayl")
    await status_msg.edit(f"{nice_label} topildi\n📦 {fmt_size(file_size)}\n⬇️ Yuklanmoqda...")
    start_time = time.time()
    cb = partial(progress_callback, status_msg=status_msg,
                 label=f"{nice_label} yuklanmoqda...", start_time=start_time)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = await user.download_media(msg, file_name=f"{DOWNLOAD_DIR}/", progress=cb)
    return file_path, mtype


async def download_story(user: Client, username: str, story_id: int, status_msg) -> tuple:
    await status_msg.edit("📖 Istoriya qidirilmoqda...")
    story = await user.get_stories(username, story_id)
    if not story:
        return None, "empty"
    media, mtype = get_media_and_type(story)
    if not media:
        return None, "empty"
    nice_label = MEDIA_LABELS.get(mtype, "📁 Fayl")
    await status_msg.edit(f"{nice_label} (istoriya)\n⬇️ Yuklanmoqda...")
    start_time = time.time()
    cb = partial(progress_callback, status_msg=status_msg,
                 label="📖 Istoriya yuklanmoqda...", start_time=start_time)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = await user.download_media(story, file_name=f"{DOWNLOAD_DIR}/", progress=cb)
    return file_path, mtype


async def send_media(bot_msg, user: Client, file_path: str, mtype: str, caption: str = ""):
    prepared_path = file_path
    compressed_path = None
    try:
        if mtype == "audio":
            prepared_path, changed = await compress_audio_file(file_path)
            if changed:
                compressed_path = prepared_path

        file_size_mb = os.path.getsize(prepared_path) / (1024 * 1024)
        user_id = bot_msg.from_user.id
        if file_size_mb > MAX_BOT_SIZE_MB:
            await _send_large_file(user, user_id, prepared_path, mtype, caption, file_size_mb)
        else:
            await _send_via_bot(bot_msg, prepared_path, mtype, caption)
    finally:
        _cleanup(file_path)
        if compressed_path and compressed_path != file_path:
            _cleanup(compressed_path)


async def _send_via_bot(bot_msg, file_path: str, mtype: str, caption: str):
    kwargs = {"quote": True, "parse_mode": "html"}
    if mtype not in ("sticker", "video_note"):
        kwargs["caption"] = caption
    if mtype == "video":
        await bot_msg.reply_video(video=file_path, **kwargs)
    elif mtype == "photo":
        await bot_msg.reply_photo(photo=file_path, **kwargs)
    elif mtype == "audio":
        await bot_msg.reply_audio(audio=file_path, **kwargs)
    elif mtype == "voice":
        await bot_msg.reply_voice(voice=file_path, **kwargs)
    elif mtype == "video_note":
        await bot_msg.reply_video_note(video_note=file_path, quote=True)
    elif mtype == "sticker":
        await bot_msg.reply_sticker(sticker=file_path, quote=True)
    elif mtype == "animation":
        await bot_msg.reply_animation(animation=file_path, **kwargs)
    else:
        await bot_msg.reply_document(document=file_path, **kwargs)


async def _send_large_file(user: Client, user_id: int, file_path: str,
                            mtype: str, caption: str, size_mb: float):
    full_caption = f"{caption}\n📦 {size_mb:.1f} MB"
    if mtype in ("video", "animation"):
        await user.send_video(user_id, file_path, caption=full_caption)
    elif mtype == "audio":
        await user.send_audio(user_id, file_path, caption=full_caption)
    elif mtype == "photo":
        await user.send_photo(user_id, file_path, caption=full_caption)
    else:
        await user.send_document(user_id, file_path, caption=full_caption)


def _cleanup(file_path: str):
    try:
        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑 O'chirildi: {file_path}")
    except Exception as e:
        logger.warning(f"Fayl o'chirishda xato: {e}")
