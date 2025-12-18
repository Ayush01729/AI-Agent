from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    # google_api_key=os.getenv("API_KEY")
    google_api_key="AIzaSyAo_uxi8_QjDFn1FJeWqPYlQDGRx24taf0"  # Replace with your actual API key
)

