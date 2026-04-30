import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("ZHIPU_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 初始化对话历史，包含系统提示
messages = [
    {
        "role": "system",
        "content": "你是一个友好的AI学习助手，专门帮助用户学习人工智能和编程。回答要简洁、清晰，多用例子。"
    }
]

print("AI 助手已就绪（输入 'quit' 退出）")
print("-" * 40)

while True:
    user_input = input("你：").strip()

    if user_input.lower() == "quit":
        print("再见！")
        break

    if not user_input:
        continue

    # 把用户消息加入历史
    messages.append({"role": "user", "content": user_input})

    # 发送完整对话历史给 GPT
    response = client.chat.completions.create(
        model="glm-4-flash",
        max_tokens=1024,
        temperature=0.7,
        messages=messages
    )

    reply = response.choices[0].message.content

    # 把 AI 回复也加入历史（下一轮需要）
    messages.append({"role": "assistant", "content": reply})

    print(f"AI：{reply}")
    print(f"（本轮 Token：{response.usage.total_tokens}，历史消息数：{len(messages)}）")
    print("-" * 40)
