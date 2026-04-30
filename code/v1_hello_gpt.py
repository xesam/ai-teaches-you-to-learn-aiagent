import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-4-flash",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "用一句话解释什么是人工智能"}
    ]
)

print("GPT 回复：")
print(response.choices[0].message.content)
print(f"\n消耗 Token：{response.usage.total_tokens}")
