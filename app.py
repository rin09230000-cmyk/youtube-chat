import streamlit as st
from utils import get_channel_from_video

st.title("💬 댓글 분석")

video_url = st.text_input(
    "유튜브 영상 링크"
)

if st.button("분석하기"):

    data = get_channel_from_video(
        video_url
    )

    if not data:
        st.error("영상을 찾을 수 없습니다.")
        st.stop()

    st.session_state[
        "channel_id"
    ] = data["channel_id"]

    st.session_state[
        "channel_name"
    ] = data["channel_title"]

    st.success(
        f"채널 저장 완료 : {data['channel_title']}"
    )

    st.info(
        "이제 수익분석 또는 성장분석으로 이동하세요."
    )
