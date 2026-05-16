import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "用一句话解释什么是人工智能"}
    ]
)

print("GPT 回复：")
print(response.choices[0].message.content)
print(f"\n消耗 Token：{response.usage.total_tokens}")
