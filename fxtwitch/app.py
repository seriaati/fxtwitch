from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

import fastapi
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

    html = f"""
    <html>
    
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#6441a5">
        <meta property="og:title" content="{clip_info.streamer} - {clip_info.title}">
        <meta property="og:type" content="video">
        <meta property="og:site_name" content="👁️ Views: {clip_info.views}">
        <meta property="og:url" content="{clip_info.url}">
        <meta property="og:video" content="{clip_info.video_url}">
        <meta property="og:video:secure_url" content="{clip_info.video_url}">
        <meta property="og:video:type" content="video/mp4">
        
        <script>
            window.onload = function() {{
                window.location.href = "{clip_info.url}";
            }}
        </script>
    </head>
    
    <body>
        <p>Redirecting you to the Twitch clip...</p>
        <p>If you are not redirected automatically, <a href="{clip_info.url}">click here</a>.</p>
    </body>
    
    </html>
    """
    return fastapi.responses.HTMLResponse(html)


@app.get("/{clip_author}/clip/{clip_id}")
async def clip_author_clip_id(
    clip_author: str, clip_id: str
) -> fastapi.responses.Response:
    try:
        return await embed_fixer(clip_id)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(
            f"https://clips.twitch.tv/{clip_author}/clip/{clip_id}"
        )


@app.get("/clip/{clip_id}")
async def clip_id(clip_id: str) -> fastapi.responses.Response:
    try:
        return await embed_fixer(clip_id)
    except Exception:
        logger.exception("Failed to fetch clip info")
        return fastapi.responses.RedirectResponse(f"https://twitch.tv/clip/{clip_id}")
