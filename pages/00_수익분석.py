import streamlit as st
from googleapiclient.discovery import build

api_key = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=api_key
)
def get_channel_data(channel_id):

    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    if not response["items"]:
        return None

    item = response["items"][0]

    stats = item["statistics"]
    snippet = item["snippet"]

    return {
        "title": snippet["title"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "subs": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0))
    }
st.title("💰 수익 분석")

if "channel_id" not in st.session_state:

    st.warning(
        "먼저 댓글 분석에서 영상을 입력하세요."
    )

    st.stop()

channel_id = st.session_state[
    "channel_id"
]

data = get_channel_data(channel_id)

st.image(
    data["thumbnail"],
    width=180
)

st.header(data["title"])

monthly_views = data["views"] * 0.03

low = (monthly_views / 1000) * 0.5
avg = (monthly_views / 1000) * 2
high = (monthly_views / 1000) * 5

c1, c2, c3 = st.columns(3)

c1.metric(
    "보수적",
    f"${low:,.0f}"
)

c2.metric(
    "평균",
    f"${avg:,.0f}"
)

c3.metric(
    "높은 추정",
    f"${high:,.0f}"
)

st.info(
    "댓글 분석에서 입력한 채널을 자동으로 사용합니다."
)
