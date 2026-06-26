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
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 한글 폰트 설정
# -----------------------------
FONT_PATH = "NanumGothic.ttf"

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)

    font_name = fm.FontProperties(
        fname=FONT_PATH
    ).get_name()

    plt.rcParams[
        "font.family"
    ] = font_name

plt.rcParams[
    "axes.unicode_minus"
] = False

# -----------------------------
# API KEY
# -----------------------------
api_key = st.secrets[
    "YOUTUBE_API_KEY"
]

# -----------------------------
# 제목
# -----------------------------
st.title(
    "📊 유튜브 댓글 분석 웹앱"
)

st.markdown("""
유튜브 댓글을 수집하여  
사용자 반응을 데이터 분석과 시각화로 살펴봅니다.
""")

# -----------------------------
# 영상 링크 입력
# -----------------------------
video_url = st.text_input(
    "유튜브 영상 링크 입력",
    placeholder="https://youtube.com/watch?v=..."
)

# -----------------------------
# 댓글 수 슬라이더
# -----------------------------
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
# 댓글 수집
# -----------------------------
# -----------------------------
# 채널 정보 가져오기
# -----------------------------
def get_channel_info(api_key, video_id):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if not response["items"]:
        return None

    snippet = response["items"][0]["snippet"]

    return {
        "channel_id": snippet["channelId"],
        "channel_name": snippet["channelTitle"]
    }
def get_comments(
    api_key,
    video_id,
    max_comments
):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    comments = []
    next_page_token = None

    progress_bar = st.progress(0)

    while len(comments) < max_comments:

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText",
            order="time"
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

            if (
                len(comments)
                >= max_comments
            ):
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
# 분석 버튼
# -----------------------------
if st.button(
    "댓글 분석 시작 🚀"
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
            "유효한 유튜브 링크가 아닙니다."
        )
        st.stop()

    with st.spinner(
        "댓글 수집 중..."
    ):

        df = get_comments(
            api_key,
            video_id,
            max_comments
        )

    if df.empty:
        st.error(
            "댓글을 가져오지 못했습니다."
        )
        st.stop()

    st.success(
        f"✅ {len(df)}개의 댓글 수집 완료!"
    )

    # -----------------------------
    # 댓글 데이터
    # -----------------------------
    st.subheader(
        "📄 수집된 댓글 데이터"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    # -----------------------------
    # 시간 데이터 처리
    # -----------------------------
    df["작성시간"] = pd.to_datetime(
        df["작성시간"]
    )

    df["시간대"] = (
        df["작성시간"]
        .dt.hour
    )

    # -----------------------------
    # 시간대별 댓글 추이
    # -----------------------------
    st.subheader(
        "🕒 시간대별 댓글 추이"
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

    ax.set_xticks(range(24))
    ax.grid(alpha=0.3)

    ax.set_title(
        "시간대별 댓글 작성 추이"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("댓글 수")

    st.pyplot(fig)

    # -----------------------------
    # 좋아요 분석 개선
    # -----------------------------
    st.subheader(
        "👍 좋아요 수 분석"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "평균 좋아요",
        round(
            df["좋아요수"].mean(),
            2
        )
    )

    col2.metric(
        "중앙값 좋아요",
        int(
            df["좋아요수"].median()
        )
    )

    col3.metric(
        "최대 좋아요",
        int(
            df["좋아요수"].max()
        )
    )

    # 이상치 제거
    threshold = (
        df["좋아요수"]
        .quantile(0.95)
    )

    filtered_likes = df[
        df["좋아요수"]
        <= threshold
    ]["좋아요수"]

    fig2, ax2 = plt.subplots(
        figsize=(12, 5)
    )

    ax2.hist(
        filtered_likes,
        bins=30
    )

    ax2.set_title(
        "좋아요 수 분포 (상위 5% 제외)"
    )

    ax2.set_xlabel(
        "좋아요 수"
    )

    ax2.set_ylabel(
        "댓글 개수"
    )

    st.pyplot(fig2)

    # -----------------------------
    # 좋아요 TOP 댓글
    # -----------------------------
    st.subheader(
        "🔥 좋아요 TOP10 댓글"
    )

    top_comments = (
        df.sort_values(
            "좋아요수",
            ascending=False
        )
        .head(10)
    )

    st.dataframe(
        top_comments[
            [
                "댓글",
                "좋아요수"
            ]
        ],
        use_container_width=True
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
        "이거", "저거",
        "정말", "오늘",
        "ㅋㅋ", "ㅎㅎ",
        "ㅠㅠ", "입니다"
    ]

    words = [
        word for word in words
        if len(word) > 1
        and word not in stopwords
    ]

    word_freq = Counter(
        words
    )

    wc = WordCloud(
        font_path=FONT_PATH,
        width=1200,
        height=600,
        background_color="white"
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
    # TOP10 단어
    # -----------------------------
    st.subheader(
        "🔥 자주 등장한 단어 TOP10"
    )

    top10 = pd.DataFrame(
        word_freq.most_common(10),
        columns=[
            "단어",
            "빈도수"
        ]
    )

    st.bar_chart(
        top10.set_index(
            "단어"
