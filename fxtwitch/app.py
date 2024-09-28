from contextlib import asynccontextmanager
from typing import AsyncGenerator

import fastapi
import httpx

from .utils import fetch_clip_info


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    app.state.client = httpx.AsyncClient()
    try:
        yield
    finally:
        await app.state.client.aclose()


app = fastapi.FastAPI(lifespan=app_lifespan)


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxtwitch")

@app.get("/{clip_author}/clip/{clip_id}")
@app.get("/clip/{clip_id}")
async def clip(clip_id: str) -> fastapi.responses.HTMLResponse:
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
