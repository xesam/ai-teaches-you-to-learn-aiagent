"""
v6 补充：纯 Python 的 Mock MCP Server

这是一个教学用的最小 MCP Server 实现，用来演示 MCP 协议本身。
全程纯 Python，不依赖任何外部运行时。

提供以下工具：
- echo: 回显文本
- add: 两数求和
- greet: 生成问候语
- read_file: 读取文件内容
- list_directory: 列出目录下的文件
- write_file: 写入文件内容

运行方式：
1. 启动 Mock Server（在一个终端）：
   python code/v6_mcp_mock_server.py

2. 修改 v6_mcp_agent.py 连接到这个 Mock Server（在另一个终端）：
   # 替换 mcp.connect() 的 command 参数为：
   command=["python", "code/v6_mcp_mock_server.py"]
"""

import sys
import json
import os


class MockMCPServer:
    """最小的 MCP Server 实现，通过 stdio 通信"""

    def __init__(self):
        self.tools = [
            {
                "name": "echo",
                "description": "返回输入的文本",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要回显的文本"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "add",
                "description": "计算两个数字的和",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "第一个数字"
                        },
                        "b": {
                            "type": "number",
                            "description": "第二个数字"
                        }
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "greet",
                "description": "生成问候语",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要问候的名字"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "read_file",
                "description": "读取指定路径的文件内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "要读取的文件路径"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "list_directory",
                "description": "列出指定目录下的文件和子目录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "要列出的目录路径"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "将内容写入指定路径的文件",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "要写入的文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的文件内容"
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        ]

    def handle_initialize(self, params):
        """处理 initialize 请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mock-mcp-server",
                "version": "1.0.0"
            }
        }

    def handle_tools_list(self, params):
        """处理 tools/list 请求"""
        return {"tools": self.tools}

    def handle_tools_call(self, params):
        """处理 tools/call 请求"""
        tool_name = params["name"]
        arguments = params["arguments"]

        if tool_name == "echo":
            result_text = arguments["text"]
        elif tool_name == "add":
            result_text = str(arguments["a"] + arguments["b"])
        elif tool_name == "greet":
            result_text = f"你好，{arguments['name']}！"
        elif tool_name == "read_file":
            try:
                with open(arguments["path"], "r", encoding="utf-8") as f:
                    result_text = f.read()
            except Exception as e:
                result_text = f"读取文件失败：{e}"
        elif tool_name == "list_directory":
            try:
                entries = os.listdir(arguments["path"])
                result_text = "\n".join(entries)
            except Exception as e:
                result_text = f"列出目录失败：{e}"
        elif tool_name == "write_file":
            try:
                with open(arguments["path"], "w", encoding="utf-8") as f:
                    f.write(arguments["content"])
                result_text = f"文件已写入：{arguments['path']}"
            except Exception as e:
                result_text = f"写入文件失败：{e}"
        else:
            result_text = f"未知工具: {tool_name}"

        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }

    def run(self):
        """运行 Server，监听 stdin 并响应"""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")

                # 处理不同的方法
                if method == "initialize":
                    result = self.handle_initialize(params)
                elif method == "tools/list":
                    result = self.handle_tools_list(params)
                elif method == "tools/call":
                    result = self.handle_tools_call(params)
                elif method == "notifications/initialized":
                    # 通知类消息，不需要响应
                    continue
                else:
                    result = {"error": f"未知方法: {method}"}

                # 返回响应（只有 request 才需要响应，notification 不需要）
                if request_id is not None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    print(json.dumps(response), flush=True)

            except Exception as e:
                if request_id is not None:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -1,
                            "message": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = MockMCPServer()
    server.run()
