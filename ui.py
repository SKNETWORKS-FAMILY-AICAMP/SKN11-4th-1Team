import streamlit as st
from streamlit_chat import message

st.set_page_config(page_title="교통사고 과실비율 챗봇", page_icon="🚦")

# 임시 응답 함수 (→ 추후 LLM 연결)
def get_response(user_input):
    return "🤖 응답예시"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("bot", "과실비율 판단봇입니다. 사고 상황을 설명해주세요.")
    ]

st.title("🤖 교통사고 과실비율 챗봇")

user_input = st.chat_input("사고 상황을 입력해주세요")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response = get_response(user_input)  # 실제 LLM 응답으로 교체 예정
    st.session_state.chat_history.append(("bot", response))

for i, (sender, msg) in enumerate(st.session_state.chat_history):
    is_user = sender == "user"
    message(msg, is_user=is_user, key=str(i))
