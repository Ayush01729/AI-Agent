import streamlit as st
from queryRunner import run_query

st.set_page_config(page_title="MallBuddy Chat", layout="wide")
st.title("Lulu Mall Shopping Assistant")


if "messages" not in st.session_state:
    st.session_state.messages = []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("Ask me about shops, offers, food, movies..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)


    bot_placeholder = st.empty()


    with bot_placeholder.container():
        with st.spinner("MallBuddy 🤖 is thinking..."):
            response = run_query(prompt)


    bot_placeholder.empty()  
    st.chat_message("assistant").markdown(response)


    st.session_state.messages.append({"role": "assistant", "content": response})
