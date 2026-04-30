"""
v7: Agent with Skills

在 v4 AgentLoop 框架基础上添加 Skill 机制：
- Skill: 封装可复用的行为模式（系统提示 + 工具组合 + 执行策略）
- 运行时动态加载：Agent 可以在对话中按需激活 Skill
- Skill 定义：Markdown 文件，包含 frontmatter 元数据和指令内容

架构：AgentLoop（v4） + SkillManager（动态加载） → 复用 Function Calling（v3）
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from v4_agent_loop import AgentLoop

load_dotenv()


class Skill:
    """
    Skill 封装了一个可复用的行为模式

    包含：
    - name: Skill 名称
    - description: 简短描述（用于 Agent 决定是否激活）
    - instructions: 详细指令（加载后注入到系统提示）
    - tools: 该 Skill 需要的工具列表（可选）
    - examples: 使用示例（可选）
    """

    def __init__(self, name: str, description: str, instructions: str,
                 tools: List[str] = None, examples: List[str] = None):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.tools = tools or []
        self.examples = examples or []

    @classmethod
    def from_file(cls, file_path: str) -> 'Skill':
        """从 Markdown 文件加载 Skill"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                instructions = parts[2].strip()
            else:
                raise ValueError(f"Invalid skill file format: {file_path}")
        else:
            raise ValueError(f"Skill file must start with frontmatter: {file_path}")

        return cls(
            name=frontmatter.get('name'),
            description=frontmatter.get('description'),
            instructions=instructions,
            tools=frontmatter.get('tools', []),
            examples=frontmatter.get('examples', [])
        )


class SkillManager:
    """
    Skill 管理器，负责：
    1. 发现和加载 Skill 定义文件
    2. 提供 Skill 列表给 AgentLoop
    3. 按需激活 Skill（注入指令到系统提示）
    """

    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            skills_dir = str(Path(__file__).parent.parent / "skills")
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self.active_skills: List[str] = []

        # 自动发现并加载所有 Skill
        self._discover_skills()

    def _discover_skills(self):
        """扫描 skills 目录，加载所有 .md 文件"""
        if not self.skills_dir.exists():
            print(f"[SkillManager] Skills 目录不存在: {self.skills_dir}")
            return

        for skill_file in self.skills_dir.glob("*.md"):
            try:
                skill = Skill.from_file(str(skill_file))
                self.skills[skill.name] = skill
                print(f"[SkillManager] 加载 Skill: {skill.name}")
            except Exception as e:
                print(f"[SkillManager] 加载失败 {skill_file}: {e}")

    def list_skills(self) -> List[Dict[str, str]]:
        """返回所有可用 Skill 的列表"""
        return [
            {"name": skill.name, "description": skill.description}
            for skill in self.skills.values()
        ]

    def activate_skill(self, skill_name: str) -> bool:
        """激活一个 Skill"""
        if skill_name not in self.skills:
            print(f"[SkillManager] Skill 不存在: {skill_name}")
            return False

        if skill_name not in self.active_skills:
            self.active_skills.append(skill_name)
            print(f"[SkillManager] 激活 Skill: {skill_name}")

        return True

    def deactivate_skill(self, skill_name: str):
        """停用一个 Skill"""
        if skill_name in self.active_skills:
            self.active_skills.remove(skill_name)
            print(f"[SkillManager] 停用 Skill: {skill_name}")

    def get_active_instructions(self) -> str:
        """获取所有激活 Skill 的指令"""
        if not self.active_skills:
            return ""

        instructions = []
        for skill_name in self.active_skills:
            skill = self.skills[skill_name]
            instructions.append(f"# Skill: {skill.name}\n\n{skill.instructions}")

        return "\n\n---\n\n".join(instructions)

    def get_required_tools(self) -> List[str]:
        """获取所有激活 Skill 需要的工具列表"""
        tools = set()
        for skill_name in self.active_skills:
            skill = self.skills[skill_name]
            tools.update(skill.tools)
        return list(tools)


class SkillEnabledAgentLoop(AgentLoop):
    """
    支持 Skill 的 AgentLoop

    扩展 v4 的 AgentLoop 类，添加：
    1. SkillManager 集成
    2. 内置 activate_skill 和 list_skills 工具
    3. 动态系统提示（包含激活的 Skill 指令）
    """

    def __init__(self, tools: list, functions: dict, skills_dir: str = None,
                 max_iterations: int = 10, verbose: bool = False):
        # skills 目录默认为项目根目录下的 skills/
        if skills_dir is None:
            skills_dir = str(Path(__file__).parent.parent / "skills")

        # 初始化 SkillManager
        self.skill_manager = SkillManager(skills_dir)

        # 添加 Skill 管理工具
        skill_tools = [
            {
                "name": "list_skills",
                "description": "列出所有可用的 Skill",
                "parameters": {}
            },
            {
                "name": "activate_skill",
                "description": "激活一个 Skill 来获得特定领域的能力",
                "parameters": {
                    "skill_name": {
                        "type": "str",
                        "description": "要激活的 Skill 名称",
                        "required": True
                    }
                }
            }
        ]

        skill_functions = {
            "list_skills": lambda: json.dumps(
                self.skill_manager.list_skills(),
                ensure_ascii=False,
                indent=2
            ),
            "activate_skill": lambda skill_name: (
                "Skill 已激活，现在你可以使用该 Skill 的能力了"
                if self.skill_manager.activate_skill(skill_name)
                else f"Skill 不存在: {skill_name}"
            )
        }

        # 合并工具和函数
        all_tools = tools + skill_tools
        all_functions = {**functions, **skill_functions}

        # 调用父类初始化
        super().__init__(
            tools=all_tools,
            functions=all_functions,
            max_iterations=max_iterations,
            verbose=verbose
        )

    def _build_system_prompt(self, base_prompt: str = None) -> str:
        """构建当前激活状态下的系统提示"""
        parts = []
        if base_prompt:
            parts.append(base_prompt)
        skill_instructions = self.skill_manager.get_active_instructions()
        if skill_instructions:
            parts.append("# 激活的 Skills\n\n" + skill_instructions)
        parts.append(self.tools_prompt)
        return "\n\n".join(parts)

    def run(self, user_message: str, system_prompt: str = None) -> str:
        """
        运行 Agent，支持动态系统提示

        系统提示 = 基础提示 + 激活的 Skill 指令 + 工具描述
        Skill 激活后在同轮循环内立即更新系统提示，无需重新发起对话。
        """
        self._base_prompt = system_prompt  # 保存供重建用
        messages = [
            {"role": "system", "content": self._build_system_prompt(system_prompt)},
            {"role": "user", "content": user_message}
        ]

        # 执行 Agent 循环（复用父类逻辑）
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n[迭代 {iteration + 1}]")

            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=messages
            )

            content = response.choices[0].message.content

            # 提取工具调用
            from v3_with_functions import extract_tool_call
            tool_call = extract_tool_call(content)

            if tool_call is None:
                # 没有工具调用，任务完成
                return content

            # 执行工具
            tool_name = tool_call["tool"]
            tool_args = tool_call["args"]

            if self.verbose:
                print(f"  [调用工具: {tool_name}，参数: {tool_args}]")

            if tool_name not in self.functions:
                result = f"错误：未找到工具 {tool_name}"
            else:
                try:
                    result = self.functions[tool_name](**tool_args)
                except Exception as e:
                    result = f"错误：工具执行失败 - {str(e)}"

            if self.verbose:
                print(f"  [返回: {result}]")

            # Skill 刚被激活：更新 system message 让指令立即生效
            if tool_name == "activate_skill":
                messages[0] = {
                    "role": "system",
                    "content": self._build_system_prompt(self._base_prompt)
                }
                if self.verbose:
                    print(f"  [系统提示已更新，新激活的 Skill 指令已注入]")

            # 把结果加入消息历史
            messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user",
                "content": f"工具 {tool_name} 的执行结果：\n{result}\n\n请继续。"
            })

        return "错误：超过最大迭代次数"


# ── 示例：使用 Skills ────────────────────────────────────────────────


if __name__ == "__main__":
    import httpx
    from bs4 import BeautifulSoup

    # ── 定义工具函数 ───────────────────────────────────────────────────

    def fetch_webpage(url: str) -> str:
        """抓取网页内容并提取纯文本"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; summarizer-bot/1.0)"}
            resp = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title else "（无标题）"
            body = soup.get_text(separator="\n", strip=True)
            content = f"页面标题：{title}\n\n{body}"
            return content[:8000] + "\n...[已截断]" if len(content) > 8000 else content
        except Exception as e:
            return f"错误：{str(e)}"

    tools = [
        {
            "name": "fetch_webpage",
            "description": "抓取指定 URL 的网页内容，返回页面标题和正文文本",
            "parameters": {
                "url": {
                    "type": "str",
                    "description": "要抓取的网页 URL",
                    "required": True
                }
            }
        }
    ]

    functions = {"fetch_webpage": fetch_webpage}

    # ── 创建 AgentLoop ──────────────────────────────────────────────────
    agent = SkillEnabledAgentLoop(
        tools=tools,
        functions=functions,
        verbose=True
    )

    # ── 测试 1: 列出可用 Skills ────────────────────────────────────────
    print("=" * 60)
    print("测试 1: 列出可用 Skills")
    print("=" * 60)
    response = agent.run("列出所有可用的 Skills")
    print(f"\n答：{response}\n")

    # ── 测试 2: 激活 Skill 后使用 ─────────────────────────────────────
    print("=" * 60)
    print("测试 2: 激活 web_summarizer skill 并总结网页")
    print("=" * 60)
    response = agent.run(
        "激活 web_summarizer skill，然后总结这个网页：https://example.com"
    )
    print(f"\n答：{response}\n")

    # ── 测试 3: 同一 Agent 实例激活另一个 Skill ────────────────────────
    print("=" * 60)
    print("测试 3: 激活 code_explainer skill 并解释代码")
    print("=" * 60)
    response = agent.run(
        "激活 code_explainer skill，然后解释这段代码：\n"
        "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)"
    )
    print(f"\n答：{response}\n")
