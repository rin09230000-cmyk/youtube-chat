import streamlit as st
from googleapiclient.discovery import build
import re

# --------------------------
# API 설정
# --------------------------

API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

st.set_page_config(
    page_title="채널 성장 분석",
    page_icon="📈",
    layout="wide"
)

st.title("📈 채널 성장 분석")

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

    if len(response["items"]) == 0:
        return None

    return response["items"][0]["snippet"]["channelId"]


# --------------------------
# 채널 정보
# --------------------------

def get_channel_data(channel_id):

    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    item = response["items"][0]

    stats = item["statistics"]

    return {
        "title": item["snippet"]["title"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "subs": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0))
    }


# --------------------------
# 성장 점수 계산
# --------------------------

def calculate_score(subs, views, videos):

    avg_views = views / max(videos, 1)

    view_ratio = avg_views / max(subs, 1)

    score = 0

    if subs >= 1000000:
        score += 40
    elif subs >= 100000:
        score += 30
    elif subs >= 10000:
        score += 20
    else:
        score += 10

    if view_ratio >= 1:
        score += 40
    elif view_ratio >= 0.5:
        score += 30
    elif view_ratio >= 0.2:
        score += 20
    else:
        score += 10

    if videos >= 500:
        score += 20
    elif videos >= 100:
        score += 15
    else:
        score += 10

    return min(score, 100)


# --------------------------
# 등급 계산
# --------------------------

def get_grade(score):

    if score >= 90:
        return "S"

    if score >= 80:
        return "A"

    if score >= 70:
        return "B"

    if score >= 60:
        return "C"

    return "D"


# --------------------------
# UI
# --------------------------

channel_input = st.session_state.get("channel")

st.title("📊 채널 분석")

st.write("현재 채널:", channel)

if st.button("성장 분석"):

    with st.spinner("분석중..."):

        channel_id = search_channel(channel_input)

        if not channel_id:
            st.error("채널을 찾을 수 없습니다.")
            st.stop()

        data = get_channel_data(channel_id)

        avg_views = data["views"] / max(data["videos"], 1)

        view_ratio = (
            avg_views /
            max(data["subs"], 1)
        ) * 100

        score = calculate_score(
            data["subs"],
            data["views"],
            data["videos"]
        )

        grade = get_grade(score)

        col1, col2 = st.columns([1, 3])

        with col1:
            st.image(
                data["thumbnail"],
                width=180
            )

        with col2:
            st.header(data["title"])

            st.metric(
                "채널 등급",
                grade
            )

            st.metric(
                "성장 점수",
                f"{score}/100"
            )

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "구독자 수",
            f"{data['subs']:,}"
        )

        c2.metric(
            "총 조회수",
            f"{data['views']:,}"
        )

        c3.metric(
            "영상 수",
            f"{data['videos']:,}"
        )

        st.divider()

        c4, c5 = st.columns(2)

        c4.metric(
            "영상당 평균 조회수",
            f"{avg_views:,.0f}"
        )

        c5.metric(
            "구독자 대비 조회율",
            f"{view_ratio:.1f}%"
        )

        st.progress(score / 100)

        if score >= 90:
            st.success(
                "🔥 매우 강력한 성장형 채널입니다."
            )

        elif score >= 75:
            st.info(
                "📈 꾸준히 성장 중인 우수 채널입니다."
            )

        else:
            st.warning(
                "📊 성장 잠재력이 있습니다."
            )
