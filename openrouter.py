import requests
import json
response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
  },
  data=json.dumps({
    "model": "meta-llama/llama-3.3-70b-instruct:free", # Optional
    "messages": [
      {
        "role": "user",
        "content": "Answer in not more than 50 words : What can you do?"
      }
    ]
  })
)

print(response.json())