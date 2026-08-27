import os
import urllib.parse

import aiohttp
from dotenv import load_dotenv

from .schema import ClipInfo

load_dotenv()

SPOO_API_KEY = os.getenv("SPOO_API_KEY")

if not SPOO_API_KEY:
    msg = "Missing required environment variable: SPOO_API_KEY"
    raise RuntimeError(msg)


async def shorten_url(client: aiohttp.ClientSession, *, url: str) -> str:
    api_url = "https://spoo.me/api/v1/shorten"
    headers = {"Authorization": f"Bearer {SPOO_API_KEY}"}
    payload = {"long_url": url}
    async with client.post(api_url, headers=headers, json=payload) as resp:
        resp.raise_for_status()
        return (await resp.json())["short_url"]


async def fetch_clip_info(client: aiohttp.ClientSession, *, clip_id: str) -> ClipInfo:
    url = "https://gql.twitch.tv/gql"
    headers = {
        "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",  # Static client ID used by Twitch web
    }
    # Inline query instead of persisted queries, whose hashes Twitch rotates
    query = """
    query($slug: ID!) {
        clip(slug: $slug) {
            title
            viewCount
            broadcaster { displayName }
            videoQualities { sourceURL }
            playbackAccessToken(params: {platform: "web", playerBackend: "mediaplayer", playerType: "site"}) {
                signature
                value
            }
        }
    }
    """
    payload = {"query": query, "variables": {"slug": clip_id}}

    async with client.post(url, headers=headers, json=payload) as response:
        data = await response.json()

    clip = data["data"]["clip"]
    video_url = clip["videoQualities"][0]["sourceURL"]
    playback_access_token = clip["playbackAccessToken"]
    video_url += f"?sig={playback_access_token['signature']}&token={urllib.parse.quote(playback_access_token['value'])}"
    video_url = await shorten_url(client, url=video_url)

    return ClipInfo(
        title=clip["title"],
        streamer=clip["broadcaster"]["displayName"],
        views=clip["viewCount"],
        video_url=video_url,
        url=f"https://clips.twitch.tv/{clip_id}",
    )
