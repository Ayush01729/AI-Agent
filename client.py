from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key= "AIzaSyDQrN3Df0dqPQ-Wu0sPuD8Os_h6X2Sq5rY"
)

