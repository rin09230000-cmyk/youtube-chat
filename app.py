import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
from googleapiclient.discovery import build
from konlpy.tag import Okt
import re
from urllib.parse import urlparse, parse_qs

# ---------------------------
# 페이지 설정
# ---------------------------
st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 유튜브 댓글 데이터 분석 웹앱")
st.markdown("유튜브 영상 댓글을 수집하고 사용자 반응을 분석합니다.")

# ---------------------------
# API KEY 입력
# ---------------------------
api_key = st.text_input(
    "YouTube API Key 입력",
    type="password"
)

# ---------------------------
# 유튜브 링크 입력
# ---------------------------
video_url = st.text_input(
    "유튜브 영상 링크 입력",
    placeholder="https://www.youtube.com/watch?v=..."
)

# 댓글 수 슬라이더
max_comments = st.slider(
    "수집할 댓글 수",
    min_value=20,
    max_value=10000,
    value=200,
    step=20
)


# ---------------------------
# 영상 ID 추출 함수
# ---------------------------
def get_video_id(url):
    parsed_url = urlparse(url)

    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]

    if parsed_url.hostname in (
        'www.youtube.com',
        'youtube.com'
    ):
        query = parse_qs(parsed_url.query)
        return query.get("v", [None])[0]

    return None


# ---------------------------
# 댓글 수집 함수
# ---------------------------
def get_comments(api_key, video_id, max_comments):

    youtube = build(
        'youtube',
        'v3',
        developerKey=api_key
    )

    comments = []

    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=100,
        textFormat='plainText'
    )

    while request and len(comments) < max_comments:

        response = request.execute()

        for item in response['items']:

            snippet = item['snippet']['topLevelComment']['snippet']

            comments.append({
                "작성시간": snippet["publishedAt"],
                "댓글": snippet["textDisplay"],
                "좋아요수": snippet["likeCount"]
            })

            if len(comments) >= max_comments:
                break

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return pd.DataFrame(comments)


# ---------------------------
# 분석 버튼
# ---------------------------
if st.button("댓글 분석 시작"):

    if not api_key:
        st.warning("API Key를 입력하세요.")
        st.stop()

    if not video_url:
        st.warning("유튜브 링크를 입력하세요.")
        st.stop()

    video_id = get_video_id(video_url)

    if not video_id:
        st.error("유효한 유튜브 링크가 아닙니다.")
        st.stop()

    with st.spinner("댓글 수집 중..."):

        df = get_comments(
            api_key,
            video_id,
            max_comments
        )

    if df.empty:
        st.error("댓글을 가져올 수 없습니다.")
        st.stop()

    st.success(f"{len(df)}개의 댓글 수집 완료!")

    st.subheader("📄 수집된 댓글 데이터")
    st.dataframe(df)

    # ---------------------------
    # 시간 데이터 변환
    # ---------------------------
    df["작성시간"] = pd.to_datetime(df["작성시간"])
    df["시간대"] = df["작성시간"].dt.hour

    # ---------------------------
    # 시간대별 댓글 수
    # ---------------------------
    st.subheader("🕒 시간대별 댓글 추이")

    time_count = (
        df["시간대"]
        .value_counts()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        time_count.index,
        time_count.values,
        marker='o'
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("댓글 수")
    ax.set_title("시간대별 댓글 작성 추이")

    st.pyplot(fig)

    # ---------------------------
    # 좋아요 분석
    # ---------------------------
    st.subheader("👍 댓글 좋아요 수 분석")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "평균 좋아요",
        round(df["좋아요수"].mean(), 2)
    )

    col2.metric(
        "최대 좋아요",
        int(df["좋아요수"].max())
    )

    col3.metric(
        "총 좋아요",
        int(df["좋아요수"].sum())
    )

    fig2, ax2 = plt.subplots(figsize=(10, 4))

    ax2.hist(
        df["좋아요수"],
        bins=30
    )

    ax2.set_title("댓글 좋아요 수 분포")
    ax2.set_xlabel("좋아요 수")
    ax2.set_ylabel("댓글 개수")

    st.pyplot(fig2)

    # ---------------------------
    # 워드클라우드
    # ---------------------------
    st.subheader("☁️ 자주 등장하는 단어")

    okt = Okt()

    text = " ".join(df["댓글"].astype(str))

    text = re.sub(
        r"[^가-힣\s]",
        "",
        text
    )

    nouns = okt.nouns(text)

    stopwords = [
        "영상", "진짜", "너무",
        "그냥", "진심", "이거",
        "저거", "합니다"
    ]

    words = [
        word for word in nouns
        if len(word) > 1
        and word not in stopwords
    ]

    word_freq = Counter(words)

    font_path = "malgun.ttf"

    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        font_path=font_path
    ).generate_from_frequencies(
        word_freq
    )

    fig3, ax3 = plt.subplots(
        figsize=(12, 5)
    )

    ax3.imshow(wc)
    ax3.axis("off")

    st.pyplot(fig3)

    # ---------------------------
    # 많이 나온 단어 TOP10
    # ---------------------------
    st.subheader("🔥 자주 등장한 단어 TOP10")

    top10 = pd.DataFrame(
        word_freq.most_common(10),
        columns=["단어", "빈도수"]
    )

    st.bar_chart(
        top10.set_index("단어")
    )
