import streamlit as st
from googleapiclient.discovery import build
import pandas as pd

# ----------------------------
# 설정
# ----------------------------
API_KEY = "여기에_유튜브_API_KEY_넣기"

youtube = build("youtube", "v3", developerKey=API_KEY)

st.set_page_config(
    page_title="유튜브 채널 수익 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 유튜브 채널 수익 분석기")
st.caption("채널명을 입력하면 예상 수익을 분석합니다. (추정치)")

# ----------------------------
# 채널 검색 함수
# ----------------------------
def search_channel(channel_name):
    request = youtube.search().list(
        q=channel_name,
        part="snippet",
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if response["items"]:
        return response["items"][0]["snippet"]["channelId"]
    return None


# ----------------------------
# 채널 정보 가져오기
# ----------------------------
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


# ----------------------------
# 예상 수익 계산
# ----------------------------
def estimate_revenue(total_views):
    # 한국 평균 CPM 대략값 기준
    low_cpm = 0.5   # 1000뷰당 0.5달러
    avg_cpm = 2
    high_cpm = 5

    monthly_views = total_views * 0.03

    low = (monthly_views / 1000) * low_cpm
    avg = (monthly_views / 1000) * avg_cpm
    high = (monthly_views / 1000) * high_cpm

    return low, avg, high


# ----------------------------
# 입력
# ----------------------------
channel_name = st.text_input(
    "유튜브 채널명을 입력하세요",
    placeholder="예: 침착맨"
)

if st.button("수익 분석하기"):
    if channel_name:
        with st.spinner("채널 분석 중..."):
            channel_id = search_channel(channel_name)

            if channel_id:
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
                        f"{data['subscribers']:,}명"
                    )

                    st.metric(
                        "총 조회수",
                        f"{data['views']:,}회"
                    )

                    st.metric(
                        "영상 수",
                        f"{data['videos']:,}개"
                    )

                st.divider()

                st.subheader("💰 예상 월 수익")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "보수적 추정",
                        f"${low:,.0f}"
                    )

                with c2:
                    st.metric(
                        "평균 추정",
                        f"${avg:,.0f}"
                    )

                with c3:
                    st.metric(
                        "높은 추정",
                        f"${high:,.0f}"
                    )

                st.info(
                    "⚠️ 실제 수익과 차이가 있을 수 있습니다. "
                    "광고 단가(CPM), 국가, 협찬, 멤버십 등에 따라 달라집니다."
                )

                # 데이터 표
                df = pd.DataFrame({
                    "항목": [
                        "구독자 수",
                        "총 조회수",
                        "영상 수"
                    ],
                    "값": [
                        f"{data['subscribers']:,}",
                        f"{data['views']:,}",
                        f"{data['videos']:,}"
                    ]
                })

                st.dataframe(df, use_container_width=True)

            else:
                st.error("채널을 찾을 수 없습니다.")
