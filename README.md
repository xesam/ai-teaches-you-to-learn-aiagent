# 从零理解 AI Agent：一个给初学者的教学项目

这个项目的目标不是做一个复杂的商用产品，而是带你**一步一步搭出一个最小可用的 AI Agent**，从而真正理解它的工作原理。

如果你已经会 Python 基础语法，这个项目会带你理解：

- 怎么调用大模型 API
- 怎么实现多轮对话
- 怎么让模型调用你写的函数
- 什么是 Agent 循环
- 怎么把这些能力组合成一个简单但真实可用的工具

## 这个项目的设计原则

本项目有一个刻意的限制：

**只依赖最基础的对话 API，通过提示词、消息历史和 Python 代码，手动实现 Function Calling、Agent 循环、Skill 加载与 MCP 集成。**

这意味着：

- 不依赖任何厂商提供的原生 `tools` / `function calling` / `skills` / `agents` 特性
- 不依赖第三方 Agent 框架来替你完成核心逻辑
- 重点是让你看清这些能力背后的**通用原理**

本仓库里的示例代码当前使用的是**智谱兼容 OpenAI 接口**的配置，所以你会看到 `ZHIPU_API_KEY`、`base_url` 和 `glm-*` 模型名。  
但这不是项目原理的一部分。只要某家模型厂商**兼容 OpenAI 风格的对话 API**，通常都可以通过替换下面这三项接入：

- `api_key`
- `base_url`
- `model`

也正因为这样，这个项目更像“教学版剖面图”，而不是一个现成的生产级框架。

## 这个项目适合谁

适合你，如果你：

- 会 Python 基础语法
- 看得懂函数、类、循环、字典
- 想理解 AI Agent 的原理，而不是直接依赖现成框架
- 愿意边读文档、边运行代码、边自己思考

## 运行前提 / 兼容厂商

运行这个项目，你至少需要：

- Python 3.9+
- 一个可用的模型 API Key
- 对应厂商提供的 **OpenAI 兼容对话 API**

本仓库当前默认示例使用的是：

- `ZHIPU_API_KEY`
- 智谱的 `base_url`
- `glm-*` 系列模型名

但这只是示例配置，不是项目原理的一部分。  
只要某家模型厂商兼容 OpenAI 风格的对话 API，通常都可以通过替换下面这三项接入：

- `api_key`
- `base_url`
- `model`

也就是说，这个项目不绑定某一家模型厂商，重点是理解通用机制。

## 学习路线

这个项目按版本递进。**每一版只比上一版多一个关键能力。**

| 版本 | 文件 | 这一版只新增了什么 |
|------|------|-------------------|
| v1 | `code/v1_hello_gpt.py` | 让 Python 和大模型对话 |
| v2 | `code/v2_conversation.py` | 记住前面的聊天记录 |
| v3 | `code/v3_with_functions.py` | 让模型“使用工具” |
| v4 | `code/v4_agent_loop.py` | 让模型连续多步完成任务 |
| v5 | `code/v5_web_summarizer.py` | 把前面的能力组合成网页总结器 |
| v6 | `code/v6_mcp_agent.py` | 用统一协议接入外部工具 |
| v7 | `code/v7_agent_with_skills.py` | 给 Agent 增加可复用的行为模块 |

推荐按下面顺序学习：

- 主线必学：`v1 -> v2 -> v3 -> v4 -> v5`
- 进阶扩展：`v6 -> v7`

如果你的目标是先搞懂 Agent 的核心原理，那么学完 `v5` 就已经足够。  
更完整的原理讲解见 [docs/00-overview.md](/Users/edy/Documents/repos/ai-teaches-me-to-learn-ai/docs/00-overview.md:1)。

## 项目结构

```bash
code/
  v1_hello_gpt.py
  v2_conversation.py
  v3_with_functions.py
  v4_agent_loop.py
  v5_web_summarizer.py
  v6_mcp_agent.py
  v7_agent_with_skills.py

docs/
  00-overview.md
  01-api-basics.md
  02-function-calling.md
  03-agent-loop.md
  04-web-summarizer.md
  05-mcp-integration.md
  06-skills.md

skills/
  code_explainer.md
  web_summarizer.md
```

- `code/`：每个版本的代码实现
- `docs/`：每个版本对应的讲解文档
- `skills/`：Skill 示例文件

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

然后编辑 `.env`，填入你的 API Key。

### 3. 从第一版开始

先读总览文档：

```bash
open docs/00-overview.md
```

再运行第一版代码：

```bash
python code/v1_hello_gpt.py
```

## 建议学习方法

推荐你每一版都按下面顺序学习：

1. 先看这一版对应的文档
2. 再运行代码，看实际输出
3. 再阅读代码
4. 最后回答这 3 个问题

- 这一版解决了什么问题？
- 它只比上一版多了什么能力？
- 如果没有这一版，下一版为什么做不出来？
