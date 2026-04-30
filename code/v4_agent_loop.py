"""
v4: Agent 循环示例

在同一个文件中定义 AgentLoop 框架核心，并演示如何使用它实现多工具协作的自主决策系统。
"""

import os
from datetime import datetime
from typing import Dict, Callable, Optional, List
from dotenv import load_dotenv
from openai import OpenAI

from v3_with_functions import extract_tool_call, build_tools_prompt

load_dotenv()


class AgentLoop:
    """
    Agent 循环核心类

    基于 v3 的单次 Function Calling 实现，添加循环控制：
    - 复用 v3 的工具调用检测和 prompt 构建
    - 添加多轮循环逻辑
    - 添加迭代次数控制
    """

    def __init__(
        self,
        tools: List[dict],
        functions: Dict[str, Callable],
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        model: str = "glm-4-flash",
        max_tokens: int = 1024,
        verbose: bool = False
    ):
        self.tools = tools
        self.functions = functions
        self.user_system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.model = model
        self.max_tokens = max_tokens
        self.verbose = verbose

        self.client = OpenAI(
            api_key=os.getenv("ZHIPU_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )

        self.tools_prompt = build_tools_prompt(self.tools)

    def run(self, user_message: str) -> str:
        """运行 AgentLoop，支持多次工具调用。"""
        full_system_prompt = (
            f"{self.user_system_prompt}\n\n{self.tools_prompt}"
            if self.user_system_prompt
            else self.tools_prompt
        )

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ]

        if self.verbose:
            print(f"\n[AgentLoop] 用户：{user_message}")

        for iteration in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages
            )

            content = response.choices[0].message.content
            tool_call = extract_tool_call(content)

            if tool_call is None:
                return content

            tool_name = tool_call["tool"]
            tool_args = tool_call["args"]

            if self.verbose:
                print(f"[AgentLoop] 迭代 {iteration + 1}: 调用 {tool_name}({tool_args})")

            if tool_name not in self.functions:
                result = f"错误：未找到工具函数 {tool_name}"
            else:
                try:
                    result = self.functions[tool_name](**tool_args)
                except Exception as e:
                    result = f"错误：工具执行失败 - {str(e)}"

            if self.verbose:
                print(f"[AgentLoop] 迭代 {iteration + 1}: 结果 = {result}")

            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": f"工具 {tool_name} 的执行结果：\n{result}\n\n请根据这个结果继续回答用户的问题。"
            })

        return f"错误：超过最大迭代次数（{self.max_iterations}），任务未完成"


# ── 1. 定义工具函数 ────────────────────────────────────────────────────
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """安全计算数学表达式"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：只支持基本数学运算"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误：{e}"


def get_day_of_year(date_str: str) -> str:
    """返回指定日期是当年第几天，date_str 格式：YYYY-MM-DD"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = date.timetuple().tm_yday
        return f"{date_str} 是 {date.year} 年第 {day_of_year} 天"
    except Exception as e:
        return f"日期解析错误：{e}"


# ── 2. 工具注册 ────────────────────────────────────────────────────────
# 函数映射表
FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_day_of_year": get_day_of_year,
}

# 简化的工具定义（用于生成 prompt）
tools = [
    {
        "name": "get_current_time",
        "description": "获取当前的日期和时间",
        "parameters": {}  # 无参数
    },
    {
        "name": "calculate",
        "description": "计算数学表达式",
        "parameters": {
            "expression": {
                "type": "str",
                "description": "数学表达式，如 '365 - 120'",
                "required": True
            }
        }
    },
    {
        "name": "get_day_of_year",
        "description": "获取某个日期是当年第几天",
        "parameters": {
            "date_str": {
                "type": "str",
                "description": "日期字符串，格式：YYYY-MM-DD",
                "required": True
            }
        }
    }
]


# ── 3. 创建 AgentLoop 实例 ──────────────────────────────────────────────
agent = AgentLoop(
    tools=tools,
    functions=FUNCTIONS,
    max_iterations=10,
    verbose=True  # 打印调试信息
)


# ── 4. 测试多步推理任务 ────────────────────────────────────────────────
if __name__ == "__main__":
    tasks = [
        "今天是几月几号？今天是今年第几天？",
        "计算 (2026 - 1990) * 365 大约是多少天？",
    ]

    for task in tasks:
        result = agent.run(task)
        print(f"[最终答案] {result}")
        print("=" * 50)
