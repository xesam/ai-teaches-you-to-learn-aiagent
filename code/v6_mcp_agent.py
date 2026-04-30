"""
v6: MCP 协议集成

在 v4 AgentLoop 框架基础上添加 MCP 协议支持：
- MCPClient: 连接 MCP Server，动态注册工具
- 复用 AgentLoop 类：无需修改，直接使用
- 示例：文件系统 MCP Server 集成

架构：MCP Server → MCPClient（转换） → AgentLoop（v4） → Function Calling（v3）
"""

import json
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
from v4_agent_loop import AgentLoop

load_dotenv()


class MCPClient:
    """
    MCP 客户端，负责：
    1. 连接 MCP Server（通过 stdio）
    2. 获取 Server 提供的工具列表
    3. 转换为 AgentLoop 框架的 tools/functions 格式
    """

    def __init__(self):
        self.servers = {}  # server_name -> process
        self.tools = []    # 聚合的工具列表
        self.functions = {}  # 工具名 -> 执行函数
        self.request_id = 0

    def connect(self, server_name: str, command: list, description: str = ""):
        """
        连接到 MCP Server

        Args:
            server_name: Server 名称（用于工具命名前缀）
            command: 启动 Server 的命令（如 ["npx", "-y", "server-name"]）
            description: Server 描述（可选）
        """
        print(f"[MCP] 连接到 {server_name}...")

        # 1. 启动 MCP Server 进程
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        self.servers[server_name] = process

        # 2. 发送 initialize 请求
        init_result = self._call_jsonrpc(process, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "ai-agent-tutorial",
                "version": "1.0.0"
            }
        })

        print(f"[MCP] {server_name} 初始化成功")
        print(f"[MCP] Server 信息: {init_result.get('serverInfo', {})}")

        # 3. 获取工具列表
        tools_result = self._call_jsonrpc(process, "tools/list", {})
        mcp_tools = tools_result.get("tools", [])

        print(f"[MCP] 发现 {len(mcp_tools)} 个工具")

        # 4. 转换并注册工具
        for mcp_tool in mcp_tools:
            self._register_tool(server_name, mcp_tool, process)

        print(f"[MCP] {server_name} 连接完成\n")

    def _call_jsonrpc(self, process, method: str, params: dict) -> dict:
        """发送 JSON-RPC 2.0 请求"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }

        # 发送请求
        request_line = json.dumps(request) + "\n"
        process.stdin.write(request_line)
        process.stdin.flush()

        # 读取响应
        response_line = process.stdout.readline()
        if not response_line:
            raise Exception(f"MCP Server 无响应")

        response = json.loads(response_line)

        if "error" in response:
            raise Exception(f"MCP 错误: {response['error']}")

        return response.get("result", {})

    def _register_tool(self, server_name: str, mcp_tool: dict, process):
        """将 MCP 工具转换为 AgentLoop 框架格式"""
        tool_name = mcp_tool["name"]
        full_name = f"{server_name}_{tool_name}"

        # 转换工具定义
        tool = {
            "name": full_name,
            "description": mcp_tool.get("description", ""),
            "parameters": self._convert_input_schema(
                mcp_tool.get("inputSchema", {})
            )
        }

        self.tools.append(tool)

        # 创建执行函数（闭包）
        def execute(**kwargs):
            result = self._call_jsonrpc(process, "tools/call", {
                "name": tool_name,
                "arguments": kwargs
            })

            # 提取文本内容
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", str(result))
            return str(result)

        self.functions[full_name] = execute

        print(f"  - {full_name}: {tool['description']}")

    def _convert_input_schema(self, input_schema: dict) -> dict:
        """将 MCP 的 inputSchema 转换为我们的参数格式"""
        if not input_schema or input_schema.get("type") != "object":
            return {}

        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        params = {}
        for param_name, param_info in properties.items():
            params[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
                "required": param_name in required
            }

        return params

    def close_all(self):
        """关闭所有 MCP Server 连接"""
        for server_name, process in self.servers.items():
            process.terminate()
            process.wait()
            print(f"[MCP] 已关闭 {server_name}")


# ── 示例：使用 MCP 文件系统 Server ────────────────────────────────────


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    # 1. 创建 MCP Client 并连接 Server
    mcp = MCPClient()

    try:
        # 连接文件系统 MCP Server（允许访问当前项目目录）
        mcp.connect(
            server_name="fs",
            command=[
                "npx", "-y",
                "@modelcontextprotocol/server-filesystem",
                str(project_root)
            ],
            description="当前项目目录文件系统操作"
        )

        # 2. 创建 AgentLoop（复用 v4 的 AgentLoop 类）
        agent = AgentLoop(
            tools=mcp.tools,
            functions=mcp.functions,
            max_iterations=10,
            verbose=True
        )

        # 3. 测试任务
        print("=" * 60)
        print("测试 1: 列出项目代码目录")
        print("=" * 60)
        response = agent.run("列出当前项目的 code 目录下有哪些文件")
        print(f"\n答：{response}\n")

        print("=" * 60)
        print("测试 2: 创建并读取文件")
        print("=" * 60)
        response = agent.run(
            "在当前项目根目录创建一个名为 mcp_demo.txt 的文件，"
            "内容是 'Hello from MCP AgentLoop!'，然后读取这个文件的内容"
        )
        print(f"\n答：{response}\n")

    finally:
        # 4. 清理：关闭所有 MCP 连接
        mcp.close_all()
