import json
import re
from datetime import datetime

from .schema import ClipInfo

# Discord silently falls back to the OG card above this many bytes
MAX_BYTES = 3000
ACCENT_COLOR = 0x9146FF

_MARKDOWN = re.compile(r"([\\*_~`|>#\[\]()<:-])")
_MENTION = re.compile(r"@(\w{3,25})")


def _escape(text: str) -> str:
    return _MARKDOWN.sub(r"\\\1", text)


def _markdown(text: str) -> str:
    """Escape Markdown in upstream text and link @mentions to Twitch."""
    parts: list[str] = []
    last = 0
    for m in _MENTION.finditer(text):
        parts.append(_escape(text[last : m.start()]))
        parts.append(f"[@{_escape(m[1])}](https://twitch.tv/{m[1].lower()})")
        last = m.end()
    parts.append(_escape(text[last:]))
    return "".join(parts)


def _cut(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def _dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _build(clip: ClipInfo, origin: str, title_length: int) -> dict:
    channel = f"https://twitch.tv/{clip.broadcaster_login}"
    check = " ✓" if clip.is_partner else ""

    subtext: list[str] = []
    if clip.followers is not None:
        subtext.append(f"👥 {clip.followers:,} followers")
    if clip.game_name and clip.game_slug:
        subtext.append(f"🎮 [{_markdown(clip.game_name)}](https://twitch.tv/directory/category/{clip.game_slug})")
    if clip.curator_name and clip.curator_login:
        subtext.append(f"✂️ Clipped by [{_markdown(clip.curator_name)}](https://twitch.tv/{clip.curator_login})")

    heading = f"### [{_markdown(clip.streamer)}]({channel}){check}"
    if subtext:
        heading += "\n-# " + " · ".join(subtext)
    header = {
        "type": 9,
        "components": [
            {"type": 10, "content": heading},
            {"type": 10, "content": f"**{_markdown(_cut(clip.title, title_length))}**"},
        ],
        "accessory": {"type": 11, "media": {"url": clip.avatar_url}},
    }

    footer = [f"👁️ **{clip.views:,}** views"]
    if clip.duration is not None:
        footer.append(f"⏱️ {clip.duration // 60}:{clip.duration % 60:02d}")
    if clip.created_at:
        created = datetime.fromisoformat(clip.created_at.replace("Z", "+00:00"))
        footer.append(f"<t:{int(created.timestamp())}:f>")
    if clip.is_featured:
        footer.append("⭐ Featured")

    buttons = [
        {"type": 2, "style": 5, "label": "Watch clip", "url": clip.url},
        {"type": 2, "style": 5, "label": "Channel", "url": channel},
    ]
    if clip.vod_id and clip.vod_offset is not None:
        o = clip.vod_offset
        buttons.append(
            {
                "type": 2,
                "style": 5,
                "label": "Full VOD",
                "url": f"https://twitch.tv/videos/{clip.vod_id}?t={o // 3600}h{o % 3600 // 60}m{o % 60}s",
            }
        )

    return {
        "component": {
            "type": 17,
            "accent_color": ACCENT_COLOR,
            "components": [
                header,
                {"type": 14, "divider": False, "spacing": 2},
                {"type": 12, "items": [{"media": {"url": f"{origin}/m/{clip.slug}/0.mp4"}}]},
                {"type": 14, "divider": True, "spacing": 2},
                {"type": 10, "content": " · ".join(footer)},
                {"type": 14, "divider": False, "spacing": 1},
                {"type": 1, "components": buttons},
            ],
        }
    }


def render_component_embed(clip: ClipInfo, origin: str) -> str | None:
    """Serialized component embed JSON, or None if it cannot fit the byte cap."""
    # A Section needs an accessory; without an avatar the embed is not worth the risk
    if not clip.slug or not clip.broadcaster_login or not clip.avatar_url:
        return None

    # Longest title that keeps the payload under the cap
    best = None
    low, high = 1, max(len(clip.title), 1)
    while low <= high:
        mid = (low + high) // 2
        payload = _dumps(_build(clip, origin, mid))
        if len(payload.encode()) <= MAX_BYTES:
            best, low = payload, mid + 1
        else:
            high = mid - 1
    return best
