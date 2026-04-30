import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedLink:
    kind: str          # "message" | "story" | "unknown"
    peer: str | int    # username yoki channel_id (int)
    msg_id: int
    story_id: Optional[int] = None


def parse_link(link: str) -> Optional[ParsedLink]:
    link = link.strip()

    # --- Istoriya: t.me/username/s/N ---
    m = re.match(r'https?://t\.me/([a-zA-Z0-9_]+)/s/(\d+)', link)
    if m:
        return ParsedLink(kind="story", peer=m.group(1), msg_id=0, story_id=int(m.group(2)))

    # --- Private kanal: t.me/c/CHANNEL_ID/MSG_ID ---
    m = re.match(r'https?://t\.me/c/(\d+)/(\d+)', link)
    if m:
        peer = int("-100" + m.group(1))
        return ParsedLink(kind="message", peer=peer, msg_id=int(m.group(2)))

    # --- Public kanal/guruh: t.me/USERNAME/MSG_ID ---
    m = re.match(r'https?://t\.me/([a-zA-Z0-9_]+)/(\d+)', link)
    if m:
        username = m.group(1)
        if username.lower() in ("joinchat", "addstickers", "share"):
            return None
        return ParsedLink(kind="message", peer=username, msg_id=int(m.group(2)))

    return None


def extract_links(text: str) -> list[str]:
    """Bir xabardagi barcha t.me havolalarni ajratib oladi."""
    pattern = r'https?://t\.me/[^\s]+'
    return re.findall(pattern, text)
