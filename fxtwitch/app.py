from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

import fastapi
import html
from aiohttp_client_cache.session import CachedSession
from aiohttp_client_cache.backends.sqlite import SQLiteBackend

from .utils import fetch_clip_info


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


async def embed_fixer(clip_id: str) -> fastapi.responses.HTMLResponse:
    clip_info = await fetch_clip_info(app.state.client, clip_id=clip_id)
    logger.info(f"Video URL: {clip_info.video_url}")

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
    </head>
    </html>
    """
    return fastapi.responses.HTMLResponse(result)


@app.get("/{clip_author}/clip/{clip_id}")
async def clip_author_clip_id(
    request: fastapi.Request, clip_author: str, clip_id: str
) -> fastapi.responses.Response:
    url = f"https://twitch.tv/{clip_author}/clip/{clip_id}"
    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    try:
        return await embed_fixer(clip_id)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(url)


@app.get("/clip/{clip_id}")
async def clip_id(request: fastapi.Request, clip_id: str) -> fastapi.responses.Response:
    url = f"https://clips.twitch.tv/{clip_id}"
    if "Discordbot" not in request.headers.get("User-Agent", ""):
        return fastapi.responses.RedirectResponse(url)

    try:
        return await embed_fixer(clip_id)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(url)
