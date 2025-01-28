import os
import urllib.parse

import aiohttp

from .schema import ClipInfo


async def shorten_url(client: aiohttp.ClientSession, *, url: str) -> str:
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": url}

    async with client.get(api_url, params=params) as response:
        return (await response.text()).strip()


async def fetch_twitch_access_token(client: aiohttp.ClientSession) -> str:
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": os.environ["TWITCH_CLIENT_ID"],
        "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
        "grant_type": "client_credentials",
    }
    async with client.post(url, params=params) as response:
        data = await response.json()
    return data["access_token"]


async def fetch_clip_info(client: aiohttp.ClientSession, *, clip_id: str) -> ClipInfo:
    access_token = await fetch_twitch_access_token(client)

    url = "https://gql.twitch.tv/gql"
    headers = {
        "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",  # Static client ID used by Twitch web
        "Authorization": f"Bearer {access_token}",
    }
    payload = [
        {
            "operationName": "VideoPlayerStreamInfoOverlayClip",
            "variables": {"slug": clip_id},
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "fcefd8b2081e39d16cbdc94bc82142df01b143bb296f0043262c44c37dbd1f63",
                }
            },
        },
        {
            "operationName": "VideoAccessToken_Clip",
            "variables": {"platform": "web", "slug": clip_id},
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "6fd3af2b22989506269b9ac02dd87eb4a6688392d67d94e41a6886f1e9f5c00f",
                }
            },
        },
    ]

    async with client.post(url, headers=headers, json=payload) as response:
        data = await response.json()

    video_url = data[1]["data"]["clip"]["videoQualities"][0]["sourceURL"]
    playback_access_token = data[1]["data"]["clip"]["playbackAccessToken"]
    video_url += f"?sig={playback_access_token['signature']}&token={urllib.parse.quote(playback_access_token['value'])}"
    video_url = await shorten_url(client, url=video_url)

    return ClipInfo(
        title=data[0]["data"]["clip"]["title"],
        streamer=data[0]["data"]["clip"]["broadcaster"]["displayName"],
        views=data[0]["data"]["clip"]["viewCount"],
        video_url=video_url,
        url=f"https://clips.twitch.tv/{clip_id}",
    )
