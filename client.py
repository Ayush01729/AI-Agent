from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key= "AIzaSyApRZgsB_iqI-yjT_CXy2hBBCfh0pPBezg"
)

