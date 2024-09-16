import os

import fastapi
import requests
import uvicorn
from dotenv import load_dotenv


def get_twitch_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": os.environ["TWITCH_CLIENT_ID"],
        "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
        "grant_type": "client_credentials",
    }
    response = requests.post(url, params=params)
    return response.json()["access_token"]


def get_clip_info(clip_id):
    access_token = get_twitch_access_token()
    url = "https://api.twitch.tv/helix/clips"
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}",
    }
    params = {"id": clip_id}
    response = requests.get(url, headers=headers, params=params)
    return response.json()["data"][0]


app = fastapi.FastAPI()


@app.get("/")
def index() -> fastapi.responses.RedirectResponse:
    return fastapi.responses.RedirectResponse("https://github.com/seriaati/fxtwitch")


@app.get("/clip/{clip_id}")
def clip(clip_id: str) -> fastapi.responses.HTMLResponse:
    clip_info = get_clip_info(clip_id)
    video_url = clip_info["thumbnail_url"].split("-preview-")[0] + ".mp4"

    resp = requests.get(video_url)
    og_type = "website" if resp.status_code != 200 else "video"

    html = f"""
    <html>
    
    <head>
        <meta property="charset" content="utf-8">
        <meta property="theme-color" content="#6441a5">
        <meta property="og:title" content="{clip_info['broadcaster_name']} - {clip_info['title']}">
        <meta property="og:type" content="{og_type}">
        <meta property="og:site_name" content="👁️ Views: {clip_info['view_count']}\n🎬 Clipped by: {clip_info['creator_name']}">
        <meta property="og:url" content="{clip_info['url']}">
        <meta property="og:video" content="{video_url}">
        <meta property="og:video:secure_url" content="{video_url}">
        <meta property="og:video:type" content="video/mp4">
        <meta property="og:image" content="{clip_info['thumbnail_url']}">
        
        <script>
            window.onload = function() {{
                window.location.href = "{clip_info['url']}";
            }}
        </script>
    </head>
    
    <body>
        <p>Redirecting you to the Twitch clip...</p>
        <p>If you are not redirected automatically, <a href="{clip_info['url']}">click here</a>.</p>
    </body>
    
    </html>
    """
    return fastapi.responses.HTMLResponse(html)


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run(app)
