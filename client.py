# ============================================================
# LLM Client Configuration
# Switch between implementations by commenting/uncommenting blocks
# ============================================================

# Current implementation: Google Gemini 2.5 Flash
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY")
    # Note: Gemini supports streaming by default, no parameter needed
)

# Alternative: OpenRouter implementation (commented out)
# from langchain_openai import ChatOpenAI
# import os
# from dotenv import load_dotenv
# 
# load_dotenv()
# 
# llm = ChatOpenAI(
#     model="meta-llama/llama-3.3-70b-instruct:free",
#     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
#     openai_api_base="https://openrouter.ai/api/v1",
#     streaming=True, 
# )



