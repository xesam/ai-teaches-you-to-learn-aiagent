# 从零理解 AI Agent：一个给初学者的教学项目

这个项目带你**一步一步搭出一个最小可用的 AI Agent**，从最简单的"调一次模型 API"，到能自主多步推理、能动态接入外部工具、能加载可复用行为模块。整个过程不靠任何 Agent 框架替你封装，全部用 Python 手搓。祛魅`AI Agent`：

- 模型只是在吐文本，不是真的在调函数；
- 模型无状态，记忆来自你每次带上完整历史；
- Skill 是"被命名、被按需注入的 system prompt 片段"
- Agent 只是一个 While 循环；

## 项目特点

**只靠最基础的对话 API，手动实现 tool、agent loop、MCP、Skill。**

这意味着：

- 不依赖厂商提供的原生 `tools` / `function calling` / `agents` / `skills` 特性
- 不依赖任何第三方 Agent 框架来替你完成核心逻辑
- 全部能力都通过 **system prompt + 消息历史 + Python 代码 + 循环控制** 拼出来

为什么这样做？因为很多人用 Agent 框架做出过东西，但说不清这些热门词汇背后到底是什么机制。这个项目的目标，就是让你从代码层面看清：

- **tool** 的本质 = 在 system prompt 里描述工具 + 解析模型输出 + 调用 Python 函数 + 回灌结果
- **agent loop** 的本质 = 在 tool 调用外面套一个 `while`，直到模型不再请求工具
- **MCP** 的本质 = 通过 JSON-RPC over stdio 让外部进程告诉你它提供哪些工具
- **Skill** 的本质 = 运行时按需把一段 markdown 注入到 system prompt 里

每个版本只新增一个核心概念，整个项目像"教学版剖面图"，不是生产级框架。

### 和生产环境写法的关系

有一点需要提前说清楚，避免误解：

**本项目手搓这些机制是为了教学，不是在推荐生产写法。**

比如项目里的工具调用，是靠"在 system prompt 里描述工具 + 用正则从模型输出里抠 JSON"实现的。真实做产品时，你应该直接用厂商提供的原生 `tools` / function calling 参数 —— 更稳定，不会因为模型偶尔不按格式输出就失败，也不用自己写解析和容错。

那为什么这里要绕远路？因为原生参数把过程封装掉了，你看不到中间发生了什么。绕一遍之后你会清楚：所谓"模型调用工具"，从头到尾只是**模型输出文本、你的程序解析文本**。理解了这层，你再用原生参数时才知道它替你做了什么。

同理，v6 的 MCP 客户端、v7 的 Skill 机制也都是手写的最小实现，用来看清协议和机制本身，而不是用来替代成熟的 SDK 和框架。

## 适合谁

适合你，如果你：

- 会 Python 基础语法，看得懂函数、类、循环、字典
- 用过 ChatGPT / Cursor 这类工具，但想搞懂背后的 Agent 机制
- 不满足于"调 LangChain 跑一个 demo"，想从零搭一遍
- 愿意边读文档、边运行代码、边自己思考

## 快速开始

只需要 4 步就能从零跑通第一版。

### 1. 创建并激活 Python 虚拟环境

需要 Python 3.9+。在项目根目录下：

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
```

激活后命令行前面会多一个 `(.venv)`，表示后续 `python`、`pip` 都用的是虚拟环境里的版本。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置大模型

本项目通过 3 个环境变量配置大模型，全部从 `.env` 读取，代码里不写死：

| 变量 | 作用 |
|------|------|
| `LLM_API_KEY` | 厂商 API Key |
| `LLM_BASE_URL` | OpenAI 兼容接口的 base URL |
| `LLM_MODEL` | 模型名 |

复制示例文件：

```bash
cp .env.example .env
```

然后编辑 `.env`，把 `LLM_API_KEY` 改成你自己的 key。`.env.example` 默认用智谱 GLM 作为开箱示例（注册一个智谱账户就能拿到免费 key）：

```
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4-plus
```

**换厂商怎么办？** 只要厂商提供 OpenAI 兼容的对话 API，把这 3 个值改掉就行 —— 这就是项目"不绑定某一家厂商"的真正含义。比如换成 DeepSeek、Moonshot、OpenAI 本家，只用改 base_url、key、模型名。

> **提示**：v3 之后会要求模型按特定 JSON 格式输出工具调用。如果你用的模型指令遵循能力较弱（比如 `glm-4-flash`），可能会偶尔不按格式输出导致工具调不起来。换成更强的模型（如 `glm-4-plus`）通常能解决。

### 4. 跑第一版

```bash
python code/v1_hello_gpt.py
```

看到模型回复 + token 数，说明环境通了。然后按学习路线一版一版往下走。

## 学习路线

整个项目按版本递进，**每一版只比上一版多一个关键能力**：

| 版本 | 文件 | 这一版只新增了什么 | 对应文档 |
|------|------|-------------------|---------|
| v1 | `code/v1_hello_gpt.py` | 让 Python 和大模型对话 | [01-api-basics.md](docs/01-api-basics.md) |
| v2 | `code/v2_conversation.py` | 记住前面的聊天记录 | [01-api-basics.md](docs/01-api-basics.md) |
| v3 | `code/v3_with_functions.py` | 让模型"使用工具" | [02-function-calling.md](docs/02-function-calling.md) |
| v4 | `code/v4_agent_loop.py` | 让模型连续多步完成任务 | [03-agent-loop.md](docs/03-agent-loop.md) |
| v5 | `code/v5_web_summarizer.py` | 把前面的能力组合成网页总结器 | [04-web-summarizer.md](docs/04-web-summarizer.md) |
| v6 | `code/v6_mcp_agent.py` | 用统一协议接入外部工具 | [05-mcp-integration.md](docs/05-mcp-integration.md) |
| v7 | `code/v7_agent_with_skills.py` | 给 Agent 增加可复用的行为模块 | [06-skills.md](docs/06-skills.md) |

推荐顺序：

- **主线必学**：`v1 → v2 → v3 → v4 → v5` —— 学完就理解了 Agent 的核心原理
- **进阶扩展**：`v6 → v7` —— 学完就理解了工具接入和行为策略怎么模块化

学完主线之前，推荐先读 [docs/00-overview.md](docs/00-overview.md) 把整体脉络打通。

**v6 额外要求**：需要本机装有 Node.js（v6 用 `npx` 启动 MCP 文件系统 server）。

## 建议学习方法

对每一版，按下面顺序学：

1. 先读对应章节的文档
2. 再运行代码，看实际输出
3. 再回头读代码
4. 最后回答这 3 个问题：
   - 这一版解决了什么问题？
   - 它只比上一版多了什么能力？
   - 如果没有这一版，下一版为什么做不出来？

## 项目结构

```
code/      # 每一版的代码实现（v1 ~ v7）
docs/      # 每一版对应的讲解文档
skills/    # v7 用到的 Skill 示例文件
```
