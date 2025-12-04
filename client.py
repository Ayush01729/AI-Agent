from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import streamlit as st


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key= st.secrets["API_KEY"]
)

