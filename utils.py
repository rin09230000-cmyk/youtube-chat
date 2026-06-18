import re
from googleapiclient.discovery import build
import streamlit as st

API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

def extract_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be\/([^?]+)",
        r"shorts\/([^?]+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def get_channel_from_video(video_url):

    video_id = extract_video_id(video_url)

    if not video_id:
        return None

    response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if not response["items"]:
        return None

    item = response["items"][0]

    return {
        "channel_id": item["snippet"]["channelId"],
        "channel_title": item["snippet"]["channelTitle"]
    }


def get_channel_data(channel_id):

    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    item = response["items"][0]

    return {
        "title": item["snippet"]["title"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "subs": int(
            item["statistics"].get(
                "subscriberCount",
                0
            )
        ),
        "views": int(
            item["statistics"].get(
                "viewCount",
                0
            )
        ),
        "videos": int(
            item["statistics"].get(
                "videoCount",
                0
            )
        )
    }
