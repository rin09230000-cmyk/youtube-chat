import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

# --------------------------
# 설정
# --------------------------

API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

st.set_page_config(
    page_title="유튜브 채널 수익 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 유튜브 댓글 분석기")

# --------------------------
# URL 처리
# --------------------------

def extract_handle(text):

    if "youtube.com/@" in text:
        match = re.search(r"@([A-Za-z0-9_.-]+)", text)

        if match:
            return match.group(1)

    if text.startswith("@"):
        return text.replace("@", "")

    return None


# --------------------------
# 채널 검색
# --------------------------

def search_channel(user_input):

    handle = extract_handle(user_input)

    query = handle if handle else user_input

    request = youtube.search().list(
        q=query,
        part="snippet",
        type="channel",
        maxResults=1
    )

    response = request.execute()

    items = response.get("items", [])

    if len(items) == 0:
        return None

    return items[0]["snippet"]["channelId"]


# --------------------------
# 채널 정보
# --------------------------

def get_channel_stats(channel_id):

    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )

    response = request.execute()

    if not response["items"]:
        return None

    item = response["items"][0]

    stats = item["statistics"]
    snippet = item["snippet"]

    return {
        "title": snippet["title"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0))
    }


# --------------------------
# 수익 계산
# --------------------------

def estimate_revenue(total_views):

    monthly_views = total_views * 0.03

    low = (monthly_views / 1000) * 0.5
    avg = (monthly_views / 1000) * 2
    high = (monthly_views / 1000) * 5

    return low, avg, high


# --------------------------
# UI
# --------------------------

channel_input = st.text_input(
    "채널명 또는 URL",
    placeholder="예: 침착맨 또는 https://youtube.com/@chimchakman"
)

if st.button("수익 분석하기"):

    if not channel_input:
        st.warning("채널명을 입력하세요")
        st.stop()

    try:

        with st.spinner("분석 중..."):

            channel_id = search_channel(channel_input)

            if not channel_id:
                st.error("채널을 찾을 수 없습니다.")
                st.stop()

            data = get_channel_stats(channel_id)

            low, avg, high = estimate_revenue(
                data["views"]
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                st.image(data["thumbnail"], width=180)

            with col2:
                st.subheader(data["title"])

                st.metric(
                    "구독자 수",
                    f"{data['subscribers']:,}"
                )

                st.metric(
                    "총 조회수",
                    f"{data['views']:,}"
                )

                st.metric(
                    "영상 수",
                    f"{data['videos']:,}"
                )

            st.divider()

            st.subheader("💰 예상 월 수익")

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
                "실제 수익과 다를 수 있습니다."
            )

    except HttpError as e:

        st.error(
            "YouTube API 오류가 발생했습니다."
        )

        st.code(str(e))

    except Exception as e:

        st.error("오류 발생")

        st.code(str(e))
