import streamlit as st

st.set_page_config(
    page_title="유튜브 분석 플랫폼",
    page_icon="📊",
    layout="wide"
)

st.title("📊 유튜브 분석 플랫폼")

st.markdown("""
### 사용 방법

1. 💬 댓글 분석으로 이동
2. 유튜브 영상 링크 입력
3. 댓글 분석 실행
4. 📈 채널 성장 분석 확인
5. 💰 수익 분석 확인

---

### 제공 기능

- 💬 댓글 감성 분석
- 💰 예상 수익 분석
- 📈 채널 성장 분석

왼쪽 메뉴에서 원하는 기능을 선택하세요.
""")

if "channel_name" in st.session_state:
    st.success(
        f"현재 선택된 채널 : {st.session_state['channel_name']}"
    )
else:
    st.info(
        "아직 선택된 채널이 없습니다."
    )
