import streamlit as st
from streamlit_chat import message
from model import model_qa_chain  # 함수 이름
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

qa_chain = model_qa_chain()  # 함수명(model_qa_chain.py에 model_qa_chain 함수 정의)

st.title("🤖 교통사고 과실비율 챗봇")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("bot", "과실비율 판단봇입니다. 사고 상황을 설명해주세요.")
    ]

user_input = st.chat_input("사고 상황을 입력해주세요")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response = qa_chain.invoke({"query": user_input})["result"]
    st.session_state.chat_history.append(("bot", response))

for i, (sender, msg) in enumerate(st.session_state.chat_history):
    message(msg, is_user=(sender == "user"), key=str(i))
