
import streamlit as st
from queryRunner import run_query
import time

st.set_page_config(page_title="MallBuddy Chat", layout="wide")

st.title("🎉Lido Mall Shopping Assistant")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display existing chat history
for chat in st.session_state.chat_history:
    if chat["type"] == "user":
        st.markdown(
            f"""
            <div style='background: #222; color: #fff; padding: 12px 16px; border-radius: 16px; margin: 8px 0; display: inline-block; float: right; clear: both;'>
                <span style='font-weight: bold; color: #90caf9;'>You:</span> {chat['message']}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='background: #333; color: #fff; padding: 12px 16px; border-radius: 16px; margin: 8px 0; display: inline-block; float: left; clear: both;'>
                <span style='font-weight: bold; color: #ffeb3b;'>MallBuddy 🤖:</span> {chat['message']}
            </div>
            """,
            unsafe_allow_html=True
        )

# Spacer to push input form to bottom
st.markdown("<br><br><br>", unsafe_allow_html=True)

# Input form at the bottom
with st.form(key="chat_form", clear_on_submit=True):
    query = st.text_input("Type your message...", key="input", placeholder="Ask me about shops, offers, food & more in Lido Mall")
    submit_button = st.form_submit_button(label="Send")

    if submit_button and query.strip():
        # Add user question immediately to chat history
        st.session_state.chat_history.append({"type": "user", "message": query})

        # Show the "Thinking..." placeholder while computing response
        placeholder = st.empty()
        with placeholder.container():
            with st.spinner("MallBuddy 🤖 is thinking... 🤔"):
                response = run_query(query)


        # Run the chatbot query (this might take a few seconds)
        # response = run_query(query)

        # Replace placeholder with actual bot response
        placeholder.empty()  # Remove the "thinking" message
        st.session_state.chat_history.append({"type": "bot", "message": response})

        # Force Streamlit to rerun and display everything nicely
        st.rerun()









