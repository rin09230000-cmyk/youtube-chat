import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from wordcloud import WordCloud
from googleapiclient.discovery import build
from collections import Counter
from urllib.parse import urlparse, parse_qs
import re
import os

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="유튜브 통합 분석기",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 한글 폰트
# -----------------------------
FONT_PATH = "NanumGothic.ttf"

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)

    font_name = fm.FontProperties(
        fname=FONT_PATH
    ).get_name()

    plt.rcParams["font.family"] = (
        font_name
    )

plt.rcParams[
    "axes.unicode_minus"
] = False

# -----------------------------
# API KEY
# -----------------------------
api_key = st.secrets[
    "YOUTUBE_API_KEY"
]

youtube = build(
    "youtube",
    "v3",
    developerKey=api_key
)

# -----------------------------
# 제목
# -----------------------------
st.title(
    "📊 유튜브 댓글 + 채널 수익 분석기"
)

st.markdown("""
유튜브 영상 링크 하나로  
**댓글 분석 + 채널 수익 분석**을 동시에 진행합니다.
""")

# -----------------------------
# 입력
# -----------------------------
video_url = st.text_input(
    "유튜브 영상 링크 입력",
    placeholder="https://youtube.com/watch?v=..."
)

max_comments = st.slider(
    "수집할 댓글 수",
    min_value=20,
    max_value=10000,
    value=200,
    step=20
)

# -----------------------------
# 영상 ID 추출
# -----------------------------
def get_video_id(url):

    parsed_url = urlparse(url)

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]

    elif parsed_url.hostname in [
        "youtube.com",
        "www.youtube.com"
    ]:

        return parse_qs(
            parsed_url.query
        ).get(
            "v",
            [None]
        )[0]

    return None


# -----------------------------
# 영상 정보
# -----------------------------
def get_video_info(video_id):

    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )

    response = request.execute()

    items = response.get(
        "items",
        []
    )

    if not items:
        return None

    return items[0]


# -----------------------------
# 채널 정보
# -----------------------------
def get_channel_stats(channel_id):

    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )

    response = request.execute()

    items = response.get(
        "items",
        []
    )

    if not items:
        return None

    return items[0]


# -----------------------------
# 댓글 수집
# -----------------------------
def get_comments(
    video_id,
    max_comments
):

    comments = []
    next_page_token = None

    progress_bar = st.progress(0)

    while len(comments) < max_comments:

        request = (
            youtube
            .commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText",
                order="time"
            )
        )

        response = request.execute()

        items = response.get(
            "items",
            []
        )

        if not items:
            break

        for item in items:

            snippet = item[
                "snippet"
            ][
                "topLevelComment"
            ][
                "snippet"
            ]

            comments.append({
                "작성시간":
                    snippet[
                        "publishedAt"
                    ],
                "댓글":
                    snippet[
                        "textDisplay"
                    ],
                "좋아요수":
                    snippet[
                        "likeCount"
                    ]
            })

            progress = min(
                len(comments)
                / max_comments,
                1.0
            )

            progress_bar.progress(
                progress
            )

            if len(comments) >= max_comments:
                break

        next_page_token = response.get(
            "nextPageToken"
        )

        if not next_page_token:
            break

    progress_bar.empty()

    return pd.DataFrame(
        comments
    )


# -----------------------------
# 수익 추정
# -----------------------------
def estimate_income(total_views):

    monthly_views = (
        total_views * 0.03
    )

    revenue_share = 0.55

    low_income = (
        monthly_views / 1000
    ) * 1 * revenue_share

    avg_income = (
        monthly_views / 1000
    ) * 3 * revenue_share

    high_income = (
        monthly_views / 1000
    ) * 7 * revenue_share

    return (
        monthly_views,
        low_income,
        avg_income,
        high_income
    )


# -----------------------------
# 분석 시작
# -----------------------------
if st.button(
    "분석 시작 🚀"
):

    if not video_url:
        st.warning(
            "유튜브 링크를 입력하세요."
        )
        st.stop()

    video_id = get_video_id(
        video_url
    )

    if not video_id:
        st.error(
            "유효한 링크가 아닙니다."
        )
        st.stop()

    # -----------------------------
    # 영상 정보
    # -----------------------------
    with st.spinner(
        "영상 분석 중..."
    ):

        video_info = get_video_info(
            video_id
        )

    if not video_info:
        st.error(
            "영상을 찾을 수 없습니다."
        )
        st.stop()

    snippet = video_info[
        "snippet"
    ]

    title = snippet["title"]

    thumbnail = snippet[
        "thumbnails"
    ]["high"]["url"]

    channel_id = snippet[
        "channelId"
    ]

    channel_title = snippet[
        "channelTitle"
    ]

    st.success(
        f"✅ {title}"
    )

    st.image(
        thumbnail,
        width=400
    )

    st.write(
        f"📺 채널: {channel_title}"
    )

    # -----------------------------
    # 댓글 수집
    # -----------------------------
    with st.spinner(
        "댓글 수집 중..."
    ):

        df = get_comments(
            video_id,
            max_comments
        )

    st.success(
        f"댓글 {len(df)}개 수집 완료!"
    )

    # -----------------------------
    # 시간 분석
    # -----------------------------
    st.subheader(
        "🕒 시간대별 댓글 추이"
    )

    df["작성시간"] = pd.to_datetime(
        df["작성시간"]
    )

    df["시간대"] = (
        df["작성시간"]
        .dt.hour
    )

    time_count = (
        df["시간대"]
        .value_counts()
        .sort_index()
    )

    fig, ax = plt.subplots(
        figsize=(12, 5)
    )

    ax.plot(
        time_count.index,
        time_count.values,
        marker="o"
    )

    ax.grid(alpha=0.3)

    ax.set_xticks(range(24))

    ax.set_title(
        "시간대별 댓글 작성 추이"
    )

    st.pyplot(fig)

    # -----------------------------
    # 좋아요 분석
    # -----------------------------
    st.subheader(
        "👍 좋아요 분석"
    )

    threshold = (
        df["좋아요수"]
        .quantile(0.95)
    )

    filtered = df[
        df["좋아요수"]
        <= threshold
    ]

    fig2, ax2 = plt.subplots(
        figsize=(12, 5)
    )

    ax2.hist(
        filtered["좋아요수"],
        bins=30
    )

    ax2.set_title(
        "좋아요 분포"
    )

    st.pyplot(fig2)

    top_comments = (
        df.sort_values(
            "좋아요수",
            ascending=False
        )
        .head(10)
    )

    st.subheader(
        "🔥 좋아요 TOP10 댓글"
    )

    st.dataframe(
        top_comments[
            [
                "댓글",
                "좋아요수"
            ]
        ]
    )

    # -----------------------------
    # 워드클라우드
    # -----------------------------
    st.subheader(
        "☁️ 워드클라우드"
    )

    text = " ".join(
        df["댓글"]
        .astype(str)
    )

    text = re.sub(
        r"[^가-힣\s]",
        " ",
        text
    )

    words = text.split()

    stopwords = [
        "영상", "진짜",
        "너무", "그냥",
        "이거", "저거"
    ]

    words = [
        w for w in words
        if len(w) > 1
        and w not in stopwords
    ]

    word_freq = Counter(
        words
    )

    wc = WordCloud(
        font_path=FONT_PATH,
        background_color="white",
        width=1200,
        height=600
    ).generate_from_frequencies(
        word_freq
    )

    fig3, ax3 = plt.subplots(
        figsize=(15, 7)
    )

    ax3.imshow(wc)
    ax3.axis("off")

    st.pyplot(fig3)

    # -----------------------------
    # 채널 수익 분석
    # -----------------------------
    st.subheader(
        "💰 채널 수익 분석"
    )

    channel_stats = get_channel_stats(
        channel_id
    )

    statistics = channel_stats[
        "statistics"
    ]

    subscribers = int(
        statistics.get(
            "subscriberCount",
            0
        )
    )

    total_views = int(
        statistics.get(
            "viewCount",
            0
        )
    )

    video_count = int(
        statistics.get(
            "videoCount",
            0
        )
    )

    (
        monthly_views,
        low_income,
        avg_income,
        high_income
    ) = estimate_income(
        total_views
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "구독자 수",
        f"{subscribers:,}"
    )

    c2.metric(
        "예상 월 수익",
        f"${avg_income:,.0f}"
    )

    c3.metric(
        "예상 연 수익",
        f"${avg_income*12:,.0f}"
    )

    st.write(
        f"📈 총 조회수: {total_views:,}"
    )

    st.write(
        f"🎬 영상 수: {video_count:,}"
    )

    income_df = pd.DataFrame({
        "수익 수준":
        ["낮음", "평균", "높음"],
        "월 수익($)":
        [
            low_income,
            avg_income,
            high_income
        ]
    })

    fig4, ax4 = plt.subplots(
        figsize=(8, 5)
    )

    ax4.bar(
        income_df["수익 수준"],
        income_df["월 수익($)"]
    )

    ax4.set_title(
        "예상 월 수익"
    )

    st.pyplot(fig4)
