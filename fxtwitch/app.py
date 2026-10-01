from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

import fastapi
import html
from aiohttp_client_cache.session import CachedSession
from aiohttp_client_cache.backends.sqlite import SQLiteBackend

from .component_embed import render_component_embed
from .schema import ClipInfo
from .utils import ClipNotFoundError, fetch_clip_info

# Clip slug -> video URL for the component embed's media redirect, since Discord
# fetches the media after the page and again later
VIDEO_URLS: dict[str, str] = {}
MAX_VIDEO_URLS = 1000


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    app.state.client = CachedSession(
        cache=SQLiteBackend(cache_name="cache.db", expire_after=3600),
    )
    try:
        yield
    finally:
        await app.state.client.close()


logger = logging.getLogger("uvicorn")
app = fastapi.FastAPI(lifespan=app_lifespan)


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxtwitch")


@app.get("/health")
async def health() -> fastapi.responses.JSONResponse:
    return fastapi.responses.JSONResponse({"status": "ok"}, status_code=200)


def remember_video_url(clip_info: ClipInfo) -> None:
    if len(VIDEO_URLS) >= MAX_VIDEO_URLS:
        VIDEO_URLS.pop(next(iter(VIDEO_URLS)))
    VIDEO_URLS[clip_info.slug] = clip_info.video_url


async def embed_fixer(clip_id: str, origin: str) -> fastapi.responses.HTMLResponse:
    clip_info = await fetch_clip_info(app.state.client, clip_id=clip_id)
    logger.info(f"Video URL: {clip_info.video_url}")

    component_embed = render_component_embed(clip_info, origin)
    if component_embed is None:
        component_embed_tag = ""
    else:
        remember_video_url(clip_info)
        component_embed_tag = f'<script id="discord:component-embed" type="application/json">{component_embed}</script>'

    result = f"""
    <html>
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#6441a5">
        <meta property="og:title" content="{html.escape(clip_info.streamer)} - {html.escape(clip_info.title)}">
        <meta property="og:type" content="video">
        <meta property="og:site_name" content="👁️ Views: {clip_info.views}">
        <meta property="og:url" content="{html.escape(clip_info.url)}">
        <meta property="og:video" content="{html.escape(clip_info.video_url)}">
        <meta property="og:video:secure_url" content="{html.escape(clip_info.video_url)}">
        <meta property="og:video:type" content="video/mp4">
        {component_embed_tag}
    </head>
    </html>
    """
    return fastapi.responses.HTMLResponse(result)


@app.get("/m/{clip_id}/0.mp4")
async def clip_media(clip_id: str) -> fastapi.responses.Response:
    video_url = VIDEO_URLS.get(clip_id)
    if video_url is None:
        try:
            clip_info = await fetch_clip_info(app.state.client, clip_id=clip_id)
        except ClipNotFoundError:
            return fastapi.responses.Response(status_code=404)
        remember_video_url(clip_info)
        video_url = clip_info.video_url
    return fastapi.responses.RedirectResponse(video_url, status_code=302)


@app.get("/{clip_author}/clip/{clip_id}")
async def clip_author_clip_id(
    request: fastapi.Request, clip_author: str, clip_id: str
) -> fastapi.responses.Response:
    url = f"https://twitch.tv/{clip_author}/clip/{clip_id}"
    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    try:
        return await embed_fixer(clip_id, str(request.base_url).rstrip("/"))
    except ClipNotFoundError:
        return fastapi.responses.RedirectResponse(url)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(url)


@app.get("/clip/{clip_id}")
async def clip_id(request: fastapi.Request, clip_id: str) -> fastapi.responses.Response:
    url = f"https://clips.twitch.tv/{clip_id}"
    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    try:
        return await embed_fixer(clip_id, str(request.base_url).rstrip("/"))
    except ClipNotFoundError:
        return fastapi.responses.RedirectResponse(url)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(url)
