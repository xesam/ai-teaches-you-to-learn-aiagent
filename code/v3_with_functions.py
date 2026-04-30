"""
v3: Function Calling 核心实现

提供可复用的 Function Calling 基础工具：
- extract_tool_call: 从模型输出中提取工具调用
- build_tools_prompt: 构建工具定义的 prompt
- execute_single_call: 执行单次函数调用流程

这些工具将被 v4 的 Agent 循环复用。
"""

import json
import re
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ── 核心工具函数（可被其他模块复用）────────────────────────────────────


def build_tools_prompt(tools: list) -> str:
    """
    构建工具定义的 system prompt

    Args:
        tools: 工具定义列表，格式：
            [{"name": "...", "description": "...", "parameters": {...}}]

    Returns:
        完整的工具定义 prompt
    """
    prompt = "你有以下工具可用：\n\n"

    for i, tool in enumerate(tools, 1):
        name = tool["name"]
        desc = tool["description"]
        params = tool.get("parameters", {})

        prompt += f"{i}. {name}("

        # 参数列表
        if params:
            param_strs = []
            for param_name, param_info in params.items():
                param_type = param_info.get("type", "any")
                param_strs.append(f"{param_name}: {param_type}")
            prompt += ", ".join(param_strs)

        prompt += ")\n"
        prompt += f"   描述：{desc}\n"

        # 参数详细说明
        if params:
            prompt += "   参数：\n"
            for param_name, param_info in params.items():
                param_desc = param_info.get("description", "")
                required = param_info.get("required", False)
                req_str = "（必填）" if required else "（可选）"
                prompt += f"   - {param_name}: {param_desc} {req_str}\n"
        else:
            prompt += "   参数：无\n"

        prompt += "\n"

    prompt += """## 调用工具的规则

**必须**使用以下 JSON 格式（用 ```json 代码块包裹），不得使用其他格式：

```json
{
  "tool": "工具名",
  "args": {"参数名": "参数值"}
}
```

无参数时 args 写空对象：
```json
{
  "tool": "list_skills",
  "args": {}
}
```

如果不需要工具，直接用自然语言回答。**不要**用函数调用风格（如 `tool_name()`）。
"""
    return prompt


def extract_tool_call(content: str) -> dict | None:
    """
    从模型输出中提取工具调用请求

    Args:
        content: 模型的输出文本

    Returns:
        如果检测到工具调用，返回 {"tool": "...", "args": {...}}
        否则返回 None
    """
    # 查找 JSON 代码块
    json_pattern = r'```json\s*\n(.*?)\n```'
    matches = re.findall(json_pattern, content, re.DOTALL)

    if not matches:
        # 兜底：查找包含 "tool" 键的 JSON 对象（支持一层嵌套）
        json_pattern2 = r'\{(?:[^{}]|\{[^{}]*\})*"tool"(?:[^{}]|\{[^{}]*\})*\}'
        matches = re.findall(json_pattern2, content, re.DOTALL)

    if not matches:
        return None

    try:
        tool_call = json.loads(matches[0])

        # 验证格式
        if "tool" not in tool_call:
            return None

        if "args" not in tool_call:
            tool_call["args"] = {}

        return tool_call
    except json.JSONDecodeError:
        return None


def execute_single_call(
    client,
    user_message: str,
    tools: list,
    functions: dict,
    system_prompt: str = None,
    model: str = "glm-4-flash",
    verbose: bool = False
) -> str:
    """
    执行单次 Function Calling 流程

    Args:
        client: OpenAI 客户端
        user_message: 用户消息
        tools: 工具定义列表
        functions: 工具名 -> 函数对象的映射
        system_prompt: 用户自定义的系统提示（可选）
        model: 模型名称
        verbose: 是否打印调试信息

    Returns:
        模型的最终回复
    """
    # 构建完整的 system prompt
    tools_prompt = build_tools_prompt(tools)
    full_system_prompt = f"{system_prompt}\n\n{tools_prompt}" if system_prompt else tools_prompt

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": user_message}
    ]

    # 第一次调用：让模型决定是否需要工具
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )

    content = response.choices[0].message.content

    # 尝试提取工具调用
    tool_call = extract_tool_call(content)

    if tool_call is None:
        # 没有工具调用，直接返回回复
        return content

    # 检测到工具调用
    tool_name = tool_call["tool"]
    tool_args = tool_call["args"]

    if verbose:
        print(f"  [检测到工具调用: {tool_name}，参数: {tool_args}]")

    # 执行工具函数
    if tool_name not in functions:
        result = f"错误：未找到工具函数 {tool_name}"
    else:
        try:
            result = functions[tool_name](**tool_args)
        except Exception as e:
            result = f"错误：工具执行失败 - {str(e)}"

    if verbose:
        print(f"  [函数返回: {result}]")

    # 把工具调用和结果加入消息历史
    messages.append({"role": "assistant", "content": content})
    messages.append({
        "role": "user",
        "content": f"工具 {tool_name} 的执行结果：\n{result}\n\n请根据这个结果回答用户的问题。"
    })

    # 第二次调用：让模型根据工具结果生成最终回答
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )

    return response.choices[0].message.content


# ── 示例：使用核心工具函数 ────────────────────────────────────────────


if __name__ == "__main__":
    # 初始化客户端
    client = OpenAI(
        api_key=os.getenv("ZHIPU_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )

    # 定义工具函数
    def get_current_time() -> str:
        """返回当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def calculate(expression: str) -> str:
        """安全计算数学表达式"""
        try:
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return "错误：只支持基本数学运算"
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"计算错误：{e}"

    # 工具注册
    tools = [
        {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {}
        },
        {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "expression": {
                    "type": "str",
                    "description": "数学表达式，如 '(3 + 5) * 2'",
                    "required": True
                }
            }
        }
    ]

    functions = {
        "get_current_time": get_current_time,
        "calculate": calculate,
    }

    # 测试
    questions = [
        "现在几点了？",
        "帮我计算 (123 + 456) * 2",
        "你好！今天天气怎么样？",
    ]

    for q in questions:
        print(f"\n问：{q}")
        answer = execute_single_call(
            client=client,
            user_message=q,
            tools=tools,
            functions=functions,
            verbose=True
        )
        print(f"答：{answer}")
