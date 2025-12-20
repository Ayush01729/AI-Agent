# Previous implementation using Google Gemini (commented out)
# from langchain_google_genai import ChatGoogleGenerativeAI
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash", 
#     google_api_key=os.getenv("GOOGLE_API_KEY")  
# )

# New implementation using OpenRouter
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct:free",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    streaming=True, 
    # default_headers={
    #     "HTTP-Referer": "http://localhost:8000",  # Optional - for ranking on openrouter.ai
    #     "X-Title": "Mall Chatbot"  # Optional - shows in rankings
    # }
)



