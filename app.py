# import streamlit as st
# from queryRunner import run_query

# st.set_page_config(page_title="MallBuddy Chat", layout="wide")
# st.title("Lido Mall Shopping Assistant")

# # Display previous messages
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Display chat history
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Get user input
# if prompt := st.chat_input("Ask me about shops, offers, food, movies..."):
#     st.chat_message("user").markdown(prompt)
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Show thinking spinner
#     with st.chat_message("assistant"):
#         with st.spinner("MallBuddy 🤖 is thinking..."):
#             response = run_query(prompt)

#         st.markdown(response)
#         st.session_state.messages.append({"role": "assistant", "content": response})

import streamlit as st
from queryRunner import run_query

st.set_page_config(page_title="MallBuddy Chat", layout="wide")
st.title("Lido Mall Shopping Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render full chat history first
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Get user input at bottom
if prompt := st.chat_input("Ask me about shops, offers, food, movies..."):
    # Immediately display user input in UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Placeholder for bot response
    bot_placeholder = st.empty()

    # Show thinking animation
    with bot_placeholder.container():
        with st.spinner("MallBuddy 🤖 is thinking..."):
            response = run_query(prompt)

    # Update placeholder with actual bot response
    bot_placeholder.empty()  # Remove spinner
    st.chat_message("assistant").markdown(response)

    # Store bot response in history
    st.session_state.messages.append({"role": "assistant", "content": response})
