import logging

from pyrogram import Client, enums, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from config import ALLOWED_USERS, MEDIA_LABELS
from utils.downloader import download_message, download_story, send_media
from utils.parser import ParsedLink, extract_links, parse_link
from utils.queue_manager import download_queue
from utils.ytdlp_downloader import detect_platform, download_external, is_external_link

logger = logging.getLogger(__name__)
BOT_COMMANDS = ["start", "help", "stats"]


def allowed():
    # If ALLOWED_USER_IDS is empty, allow all private users.
    if not ALLOWED_USERS:
        return filters.private
    return filters.user(ALLOWED_USERS) & filters.private


def _home_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📘 Help"), KeyboardButton("📊 Stats")],
            [KeyboardButton("🧹 Clear Queue")],
        ],
        resize_keyboard=True,
    )


def _start_message() -> str:
    return (
        "<b>Welcome to Monster Media Bot</b>\n\n"
        "⚡ <b>Fast:</b> optimized queue for concurrent users\n"
        "🎵 <b>Smart audio:</b> auto compression before upload\n"
        "🌐 <b>Supports:</b> Telegram + major social platforms\n\n"
        "Send a link and choose a premium download mode below."
    )


def _help_message() -> str:
    return (
        "<b>How to use</b>\n\n"
        "<b>External links:</b> send URL, then select HD/720p/480p/Audio.\n"
        "<b>Telegram links:</b> send URL, then select Video or Audio.\n\n"
        "<b>Examples</b>\n"
        "<code>https://t.me/c/1234567890/293</code>\n"
        "<code>https://t.me/channel/100</code>\n"
        "<code>https://t.me/user/s/5</code>\n\n"
        "Large files are delivered through user session when Bot API limits are exceeded."
    )


def _ext_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 HD (Best)", callback_data=f"eq|best|{url}")],
            [
                InlineKeyboardButton("📺 720p", callback_data=f"eq|720|{url}"),
                InlineKeyboardButton("📱 480p", callback_data=f"eq|480|{url}"),
            ],
            [InlineKeyboardButton("🎵 Audio (Compressed MP3)", callback_data=f"eq|audio|{url}")],
        ]
    )


def _tg_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 Video", callback_data=f"tq|video|{url}")],
            [InlineKeyboardButton("🎵 Audio (Compressed MP3)", callback_data=f"tq|audio|{url}")],
        ]
    )


def register_start(bot: Client):
    @bot.on_message(allowed() & filters.command("start"))
    async def cmd_start(_, msg: Message):
        await msg.reply(
            _start_message(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_home_keyboard(),
        )


def register_help(bot: Client):
    @bot.on_message(allowed() & filters.command("help"))
    async def cmd_help(_, msg: Message):
        await msg.reply(
            _help_message(),
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_home_keyboard(),
        )


def register_stats(bot: Client):
    @bot.on_message(allowed() & filters.command("stats"))
    async def cmd_stats(_, msg: Message):
        user_id = msg.from_user.id
        s = download_queue.stats.get(user_id, {"done": 0, "failed": 0})
        q = download_queue.queue_size(user_id)
        await msg.reply(
            f"<b>Your stats</b>\n\n"
            f"✅ Success: <b>{s.get('done', 0)}</b>\n"
            f"❌ Failed: <b>{s.get('failed', 0)}</b>\n"
            f"⏳ Queue: <b>{q}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_home_keyboard(),
        )


def register_quick_actions(bot: Client):
    @bot.on_message(allowed() & filters.regex(r"^📘 Help$"))
    async def help_button(_, msg: Message):
        await msg.reply(_help_message(), parse_mode=enums.ParseMode.HTML, reply_markup=_home_keyboard())

    @bot.on_message(allowed() & filters.regex(r"^📊 Stats$"))
    async def stats_button(_, msg: Message):
        user_id = msg.from_user.id
        s = download_queue.stats.get(user_id, {"done": 0, "failed": 0})
        q = download_queue.queue_size(user_id)
        await msg.reply(
            f"<b>Your stats</b>\n\n"
            f"✅ Success: <b>{s.get('done', 0)}</b>\n"
            f"❌ Failed: <b>{s.get('failed', 0)}</b>\n"
            f"⏳ Queue: <b>{q}</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_home_keyboard(),
        )

    @bot.on_message(allowed() & filters.regex(r"^🧹 Clear Queue$"))
    async def clear_queue_button(_, msg: Message):
        removed = await download_queue.clear_user_queue(msg.from_user.id)
        await msg.reply(
            f"🧹 Pending queue cleaned: <b>{removed}</b> item(s) removed.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_home_keyboard(),
        )


def register_link_handler(bot: Client, user: Client):
    @bot.on_message(allowed() & filters.text & ~filters.command(BOT_COMMANDS))
    async def handle_text(_, msg: Message):
        text = msg.text.strip()

        if is_external_link(text):
            platform = detect_platform(text)
            await msg.reply(
                f"{platform} link accepted.\n<b>Select quality:</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=_ext_keyboard(text),
            )
            return

        links = extract_links(text)
        if not links:
            await msg.reply(
                "No valid link found.\n\n"
                "Examples:\n"
                "<code>https://t.me/c/1234567890/293</code>\n"
                "<code>https://youtube.com/watch?v=...</code>",
                parse_mode=enums.ParseMode.HTML,
            )
            return

        for link in links:
            parsed = parse_link(link)
            if not parsed:
                await msg.reply(f"❌ Invalid link:\n<code>{link}</code>", parse_mode=enums.ParseMode.HTML)
                continue
            await msg.reply(
                "Telegram link accepted.\n<b>Select output mode:</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=_tg_keyboard(link),
            )

    @bot.on_callback_query(filters.user(ALLOWED_USERS))
    async def handle_callback(_, cb: CallbackQuery):
        data = cb.data or ""

        if data.startswith("eq|"):
            _, quality, url = data.split("|", 2)
            label = {"best": "HD", "720": "720p", "480": "480p", "audio": "Audio"}.get(quality, quality)
            platform = detect_platform(url)
            await cb.message.edit_text(f"{platform} — <b>{label}</b> queued ⏳", parse_mode=enums.ParseMode.HTML)
            await cb.answer()
            await _enqueue_external(user, cb.message, url, quality)
            return

        if data.startswith("tq|"):
            _, mode, url = data.split("|", 2)
            label = "Video" if mode == "video" else "Audio"
            await cb.message.edit_text(f"Telegram — <b>{label}</b> queued ⏳", parse_mode=enums.ParseMode.HTML)
            await cb.answer()
            parsed = parse_link(url)
            if not parsed:
                await cb.message.edit_text("❌ Invalid Telegram link.")
                return
            await _enqueue_tg(user, cb.message, parsed, url, audio_only=(mode == "audio"))
            return

        await cb.answer()


async def _enqueue_tg(user: Client, msg: Message, parsed: ParsedLink, link: str, audio_only: bool = False):
    q = download_queue.queue_size(msg.from_user.id)
    if q > 0:
        await msg.reply(f"⏳ Queue position: <b>{q + 1}</b>", parse_mode=enums.ParseMode.HTML)

    async def task():
        await _process_tg(user, msg, parsed, link, audio_only)

    await download_queue.add(msg.from_user.id, task)


async def _enqueue_external(user: Client, msg: Message, url: str, quality: str):
    q = download_queue.queue_size(msg.from_user.id)
    if q > 0:
        await msg.reply(f"⏳ Queue position: <b>{q + 1}</b>", parse_mode=enums.ParseMode.HTML)

    async def task():
        await _process_external(user, msg, url, quality)

    await download_queue.add(msg.from_user.id, task)


async def _process_tg(user: Client, bot_msg: Message, parsed: ParsedLink, link: str, audio_only: bool = False):
    status = await bot_msg.reply("⏳ Processing Telegram content...")
    try:
        if parsed.kind == "story":
            file_path, mtype = await download_story(user, str(parsed.peer), parsed.story_id, status)
        else:
            file_path, mtype = await download_message(user, parsed.peer, parsed.msg_id, status)

        if file_path is None:
            await status.edit("❌ Media not found.")
            return
        if mtype == "text":
            await status.edit(f"📝 <b>Message</b>\n\n{file_path}", parse_mode=enums.ParseMode.HTML)
            return
        if mtype == "empty":
            await status.edit("❌ Empty message.")
            return

        if audio_only and mtype == "video":
            mtype = "audio"

        await status.edit("📤 Uploading...")
        await send_media(bot_msg, user, file_path, mtype, caption=f"{MEDIA_LABELS.get(mtype, '📁')} | {link}")
        await status.delete()
    except Exception as e:
        await _handle_error(status, str(e))


async def _process_external(user: Client, bot_msg: Message, url: str, quality: str):
    platform = detect_platform(url)
    label = {"best": "HD", "720": "720p", "480": "480p", "audio": "Audio"}.get(quality, quality)
    status = await bot_msg.reply(f"⏳ {platform} ({label}) downloading...")
    try:
        file_path, mtype = await download_external(url, status, quality)
        if not file_path:
            await status.edit("❌ Media not found.")
            return

        await status.edit("📤 Uploading...")
        await send_media(bot_msg, user, file_path, mtype, caption=f"{platform} | {label} | {url[:64]}")
        await status.delete()
    except Exception as e:
        await _handle_error(status, str(e))


async def _handle_error(status_msg: Message, err: str):
    hints = {
        "CHAT_RESTRICTED": "Downloading from that chat is restricted.",
        "MESSAGE_ID_INVALID": "Message not found or deleted.",
        "PEER_ID_INVALID": "Chat/channel is not accessible for this account.",
        "FLOOD_WAIT": "Telegram rate limit hit. Please retry shortly.",
        "STORY_ID_INVALID": "Story is unavailable or expired.",
        "Private video": "This video is private.",
        "unavailable": "Media unavailable or removed.",
    }
    hint = next((v for k, v in hints.items() if k in err), err[:200])
    try:
        await status_msg.edit(f"❌ <b>Error:</b>\n<code>{hint}</code>", parse_mode=enums.ParseMode.HTML)
    except Exception:
        logger.exception("Failed to edit error status message")


def register_all(bot: Client, user: Client):
    register_start(bot)
    register_help(bot)
    register_stats(bot)
    register_quick_actions(bot)
    register_link_handler(bot, user)
