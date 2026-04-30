import os

API_ID          = int(os.environ["API_ID"])
API_HASH        = os.environ["API_HASH"]
BOT_TOKEN       = os.environ["BOT_TOKEN"]
SESSION_STRING  = os.environ["SESSION_STRING"]
ALLOWED_USERS   = [int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").split(",") if x]

DOWNLOAD_DIR    = "downloads"
MAX_BOT_SIZE_MB = 50          # Bot API limiti
PROGRESS_UPDATE_EVERY = 3     # sekundda bir marta progress yangilanadi
MAX_CONCURRENT_TASKS = int(os.environ.get("MAX_CONCURRENT_TASKS", "6"))
AUDIO_TARGET_BITRATE = os.environ.get("AUDIO_TARGET_BITRATE", "96k")
AUDIO_TARGET_CODEC = os.environ.get("AUDIO_TARGET_CODEC", "libmp3lame")
AUDIO_OUTPUT_FORMAT = os.environ.get("AUDIO_OUTPUT_FORMAT", "mp3")
BROWSER_COOKIES = os.environ.get("BROWSER_COOKIES", "")

# Media type nomlari (log va xabarlar uchun)
MEDIA_LABELS = {
    "video"       : "🎬 Video",
    "photo"       : "🖼 Rasm",
    "document"    : "📄 Fayl",
    "audio"       : "🎵 Audio",
    "voice"       : "🎤 Ovozli xabar",
    "video_note"  : "⭕ Video-xabar",
    "sticker"     : "😊 Stiker",
    "animation"   : "🎞 GIF",
    "story"       : "📖 Istoriya",
}
