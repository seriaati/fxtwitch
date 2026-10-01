from dataclasses import dataclass


@dataclass(kw_only=True)
class ClipInfo:
    title: str
    streamer: str
    views: int
    video_url: str
    url: str

    # Extra fields for the Discord component embed
    slug: str = ""
    broadcaster_login: str = ""
    avatar_url: str | None = None
    is_partner: bool = False
    followers: int | None = None
    game_name: str | None = None
    game_slug: str | None = None
    curator_name: str | None = None
    curator_login: str | None = None
    created_at: str | None = None
    duration: int | None = None
    is_featured: bool = False
    vod_id: str | None = None
    vod_offset: int | None = None
