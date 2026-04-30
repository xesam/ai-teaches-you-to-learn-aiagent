"""
v5: 网页总结工具

演示如何使用 AgentLoop 框架构建真实应用。
只需定义工具函数，其他逻辑完全复用框架。
"""

import httpx
from bs4 import BeautifulSoup
from v4_agent_loop import AgentLoop


# ── 1. 定义工具函数 ────────────────────────────────────────────────────
MAX_CONTENT_CHARS = 8000


def fetch_webpage(url: str) -> str:
    """抓取网页内容并提取纯文本"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; summarizer-bot/1.0)"}
        response = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 移除噪声标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # 提取标题和正文
        title = soup.title.string.strip() if soup.title else "（无标题）"
        body_text = soup.get_text(separator="\n", strip=True)

        # 合并并截断
        content = f"页面标题：{title}\n\n{body_text}"
        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + "\n...[内容已截断，仅显示前8000字符]"

        return content

    except httpx.TimeoutException:
        return "错误：请求超时（超过15秒），该网页响应过慢"
    except httpx.HTTPStatusError as e:
        return f"错误：HTTP {e.response.status_code}，无法访问该网页"
    except Exception as e:
        return f"错误：{str(e)}"


# ── 2. 工具注册 ────────────────────────────────────────────────────────
FUNCTIONS = {"fetch_webpage": fetch_webpage}

# 简化的工具定义（用于生成 prompt）
tools = [
    {
        "name": "fetch_webpage",
        "description": "抓取指定URL的网页内容，返回页面标题和正文文本",
        "parameters": {
            "url": {
                "type": "str",
                "description": "要抓取的网页URL，必须以http://或https://开头",
                "required": True
            }
        }
    }
]


# ── 3. 系统提示 ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """你是一个网页内容总结助手。
当用户提供网页URL时，使用 fetch_webpage 工具获取内容，然后生成结构清晰的中文摘要。

摘要格式：
1. 【核心主题】一句话说明文章讲什么
2. 【主要内容】3-5个要点（用"-"列出）
3. 【关键信息】数字、日期、人名等重要细节

如果网页无法访问，告知用户原因。"""


# ── 4. 创建 AgentLoop 实例 ──────────────────────────────────────────────
agent = AgentLoop(
    tools=tools,
    functions=FUNCTIONS,
    system_prompt=SYSTEM_PROMPT,
    max_iterations=5,
    verbose=True
)


# ── 5. 交互式入口 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("网页总结工具（输入 'quit' 退出）")
    print("用法：直接输入网页URL，或输入'总结 <URL>'")
    print("-" * 50)

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() == "quit":
            print("再见！")
            break

        if not user_input:
            continue

        print("AI：（处理中...）")
        result = agent.run(user_input)
        print(f"AI：{result}")
