from dataclasses import dataclass


@dataclass(kw_only=True)
class ClipInfo:
    title: str
    streamer: str
    views: int
    video_url: str
    url: str
