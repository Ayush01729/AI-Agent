import streamlit as st
from queryRunner import run_query

st.set_page_config(page_title="MallBuddy Chat", layout="wide")
st.title("Lido Mall Shopping Assistant")

# Display previous messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user input
if prompt := st.chat_input("Ask me about shops, offers, food, movies..."):
    # Display user message immediately
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show thinking spinner
    with st.chat_message("assistant"):
        with st.spinner("MallBuddy 🤖 is thinking..."):
            response = run_query(prompt)

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})






