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

    html = f"""
    <html>
    
    <head>
    <meta property="og:title" content="{clip_info['broadcaster_name']} - {clip_info['title']}">
    <meta property="og:type" content="video">
    <meta property="og:description" content="👁️ Views: {clip_info['view_count']}\n🎬 Clipped by: {clip_info['creator_name']}">
    <meta property="og:url" content="{clip_info['url']}">
    <meta property="og:video" content="{video_url}">
    <meta property="og:site_name" content="Twitch">
    </head>
    
    </html>
    """
    return fastapi.responses.HTMLResponse(html)


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run(app)
