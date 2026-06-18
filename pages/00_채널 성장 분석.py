import streamlit as st
from utils import get_channel_data

st.title("📈 채널 성장 분석")

if "channel_id" not in st.session_state:

    st.warning(
        "먼저 댓글 분석에서 영상을 입력하세요."
    )

    st.stop()

channel_id = st.session_state[
    "channel_id"
]

data = get_channel_data(channel_id)

avg_views = (
    data["views"] /
    max(data["videos"], 1)
)

view_ratio = (
    avg_views /
    max(data["subs"], 1)
) * 100

score = 0

if data["subs"] >= 1000000:
    score += 40
elif data["subs"] >= 100000:
    score += 30
else:
    score += 20

if view_ratio >= 100:
    score += 40
elif view_ratio >= 50:
    score += 30
else:
    score += 20

if data["videos"] >= 500:
    score += 20
else:
    score += 10

if score >= 90:
    grade = "S"
elif score >= 80:
    grade = "A"
elif score >= 70:
    grade = "B"
else:
    grade = "C"

st.image(
    data["thumbnail"],
    width=180
)

st.header(data["title"])

c1, c2 = st.columns(2)

c1.metric(
    "채널 등급",
    grade
)

c2.metric(
    "성장 점수",
    f"{score}/100"
)

st.progress(score / 100)

c1, c2, c3 = st.columns(3)

c1.metric(
    "구독자",
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

st.metric(
    "영상당 평균 조회수",
    f"{avg_views:,.0f}"
)
