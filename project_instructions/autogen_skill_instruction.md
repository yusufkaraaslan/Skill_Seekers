# AutoGen Multi-Agent Framework Skill

> 基於 [AutoGen 官方文件](https://microsoft.github.io/autogen/stable/) 與 [GitHub 原始碼](https://github.com/microsoft/autogen) 整理的完整開發指南

## 適用情境

當使用者需要以下協助時使用此指令：
- 建立 AutoGen 多代理 AI 應用
- 設計代理間協作與對話流程
- 整合 OpenAI/Azure OpenAI 模型
- 實作工具調用與代碼執行
- 建構 GroupChat、Swarm、MagenticOne 團隊
- 從 AutoGen 0.2 遷移至新版本

---

## 1. 概述

AutoGen 是 Microsoft 開發的多代理 AI 框架，用於建立可自主運作或與人類協作的 AI 應用程式。

### 專案統計 (2025)

| 指標 | 數值 |
|------|------|
| GitHub Stars | 40k+ |
| 維護者 | Microsoft |
| 語言 | Python / .NET |
| License | MIT |
| Python 版本 | 3.10+ |

### 核心特色

- **分層架構**: Core API → AgentChat API → Extensions API
- **多代理協作**: 支援多種團隊模式 (RoundRobin, Selector, Swarm, MagenticOne)
- **工具整合**: 自訂工具、程式碼執行、MCP 協議
- **跨語言**: 支援 Python 和 .NET
- **開發工具**: AutoGen Studio (無程式碼 GUI)、AgBench (效能評測)

### 框架層級

```
┌─────────────────────────────────────────┐
│           Extensions API                │  ← LLM 客戶端、工具、程式碼執行
├─────────────────────────────────────────┤
│           AgentChat API                 │  ← 高階 API，快速原型開發
├─────────────────────────────────────────┤
│             Core API                    │  ← 訊息傳遞、事件驅動、分散式執行
└─────────────────────────────────────────┘
```

---

## 2. 安裝與設定

### 2.1 基本安裝

```bash
# 需要 Python 3.10 或更高版本
pip install -U "autogen-agentchat" "autogen-ext[openai]"
```

### 2.2 完整安裝 (含 Azure 支援)

```bash
pip install -U "autogen-agentchat" "autogen-ext[openai,azure]"
```

### 2.3 AutoGen Studio (無程式碼 GUI)

```bash
pip install -U "autogenstudio"

# 啟動
autogenstudio ui --port 8080
```

### 2.4 開發安裝 (從原始碼)

```bash
git clone https://github.com/microsoft/autogen.git
cd autogen/python
pip install -e packages/autogen-core
pip install -e packages/autogen-agentchat
pip install -e "packages/autogen-ext[openai]"
```

### 2.5 環境變數設定

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

---

## 3. 核心概念

### 3.1 代理 (Agent)

代理是 AutoGen 的基本單位，具有以下特性：
- 接收和發送訊息
- 擁有系統提示詞
- 可調用工具
- 可與其他代理協作

### 3.2 團隊 (Team)

團隊是多個代理的組合，支援不同的協作模式：

| 團隊類型 | 說明 | 適用場景 |
|---------|------|---------|
| `RoundRobinGroupChat` | 輪流發言 | 固定流程、序列任務 |
| `SelectorGroupChat` | LLM 選擇下一個發言者 | 動態協作、研究任務 |
| `Swarm` | 代理間任務交接 | 狀態機、部門工作流 |
| `MagenticOneGroupChat` | 複雜任務協調者 | 開放式問題、網路研究 |

### 3.3 終止條件 (Termination)

控制對話何時結束：

```python
from autogen_agentchat.conditions import (
    MaxMessageTermination,      # 達到最大訊息數
    TextMentionTermination,     # 包含特定文字
    HandoffTermination,         # 交接給特定代理
    SourceMatchTermination,     # 特定代理發言
    StopMessageTermination,     # 收到停止訊息
)
```

---

## 4. AgentChat API (快速入門)

### 4.1 建立簡單代理

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    # 建立模型客戶端
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 建立代理
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message="You are a helpful assistant.",
    )

    # 執行任務
    result = await agent.run(task="What is the capital of France?")
    print(result)

asyncio.run(main())
```

### 4.2 使用工具的代理

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 定義工具函數
async def get_weather(city: str) -> str:
    """Get the weather for a city."""
    # 實際應用中呼叫天氣 API
    return f"The weather in {city} is sunny, 25°C."

async def calculate(expression: str) -> str:
    """Calculate a math expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[get_weather, calculate],
        system_message="You are a helpful assistant with access to weather and calculator tools.",
        reflect_on_tool_use=True,  # 讓模型總結工具輸出
    )

    # 使用 Console 顯示串流輸出
    await Console(agent.run_stream(task="What's the weather in Tokyo and what is 15 * 23?"))

asyncio.run(main())
```

### 4.3 自訂工具類別

```python
from autogen_core import CancellationToken
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum number of results")

class SearchTool(BaseTool[SearchInput, str]):
    def __init__(self):
        super().__init__(
            args_type=SearchInput,
            return_type=str,
            name="web_search",
            description="Search the web for information",
        )

    async def run(self, args: SearchInput, cancellation_token: CancellationToken) -> str:
        # 實作搜尋邏輯
        return f"Found {args.max_results} results for: {args.query}"

# 使用
agent = AssistantAgent(
    name="researcher",
    model_client=model_client,
    tools=[SearchTool()],
)
```

---

## 5. 團隊模式

### 5.1 RoundRobinGroupChat (輪流發言)

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 建立多個代理
    writer = AssistantAgent(
        name="writer",
        model_client=model_client,
        system_message="You are a creative writer. Write engaging content.",
    )

    editor = AssistantAgent(
        name="editor",
        model_client=model_client,
        system_message="You are an editor. Review and improve the content.",
    )

    critic = AssistantAgent(
        name="critic",
        model_client=model_client,
        system_message="You are a critic. Provide constructive feedback.",
    )

    # 建立團隊
    termination = MaxMessageTermination(max_messages=6)
    team = RoundRobinGroupChat(
        participants=[writer, editor, critic],
        termination_condition=termination,
    )

    # 執行任務
    await Console(team.run_stream(task="Write a short story about AI."))

asyncio.run(main())
```

### 5.2 SelectorGroupChat (智慧選擇)

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 專業代理
    planner = AssistantAgent(
        name="planner",
        model_client=model_client,
        system_message="""You are a planning agent.
        Break down complex tasks into steps.
        Coordinate with other agents to complete the task.""",
    )

    researcher = AssistantAgent(
        name="researcher",
        model_client=model_client,
        system_message="You research and gather information.",
    )

    analyst = AssistantAgent(
        name="analyst",
        model_client=model_client,
        system_message="You analyze data and provide insights. Say TERMINATE when done.",
    )

    # SelectorGroupChat 使用 LLM 選擇下一個發言者
    termination = TextMentionTermination("TERMINATE")
    team = SelectorGroupChat(
        participants=[planner, researcher, analyst],
        model_client=model_client,  # 用於選擇下一個發言者
        termination_condition=termination,
    )

    await Console(team.run_stream(task="Research the latest AI trends and provide a summary."))

asyncio.run(main())
```

### 5.3 Swarm (任務交接)

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import HandoffTermination, MaxMessageTermination
from autogen_agentchat.teams import Swarm
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 客服代理 - 可交接給專家
    support_agent = AssistantAgent(
        name="support",
        model_client=model_client,
        handoffs=["billing_expert", "technical_expert", "user"],
        system_message="""You are a customer support agent.
        - For billing issues, handoff to billing_expert
        - For technical issues, handoff to technical_expert
        - When resolved, handoff to user""",
    )

    billing_expert = AssistantAgent(
        name="billing_expert",
        model_client=model_client,
        handoffs=["support", "user"],
        system_message="You handle billing and payment issues.",
    )

    technical_expert = AssistantAgent(
        name="technical_expert",
        model_client=model_client,
        handoffs=["support", "user"],
        system_message="You handle technical support issues.",
    )

    # Swarm 團隊
    termination = HandoffTermination(target="user") | MaxMessageTermination(10)
    team = Swarm(
        participants=[support_agent, billing_expert, technical_expert],
        termination_condition=termination,
    )

    await Console(team.run_stream(task="I was charged twice for my subscription."))

asyncio.run(main())
```

### 5.4 MagenticOneGroupChat (複雜任務)

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 代碼執行代理
    code_executor = CodeExecutorAgent(
        name="code_executor",
        code_executor=LocalCommandLineCodeExecutor(work_dir="./workspace"),
    )

    # 研究代理
    researcher = AssistantAgent(
        name="researcher",
        model_client=model_client,
        system_message="You research information and gather data.",
    )

    # MagenticOne 團隊 - 自動協調複雜任務
    team = MagenticOneGroupChat(
        participants=[researcher, code_executor],
        model_client=model_client,
    )

    await Console(team.run_stream(
        task="Analyze the top 5 programming languages by popularity and create a bar chart."
    ))

asyncio.run(main())
```

---

## 6. 模型客戶端

### 6.1 OpenAI

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 基本使用
client = OpenAIChatCompletionClient(model="gpt-4o")

# 自訂設定
client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key="sk-...",  # 可選，預設從環境變數讀取
    temperature=0.7,
    max_tokens=4096,
)
```

### 6.2 Azure OpenAI

```python
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

client = AzureOpenAIChatCompletionClient(
    model="gpt-4o",
    azure_deployment="your-deployment-name",
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-02-15-preview",
    # api_key 從 AZURE_OPENAI_API_KEY 環境變數讀取
)
```

### 6.3 其他模型提供者

```python
# Anthropic Claude
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

client = AnthropicChatCompletionClient(model="claude-3-5-sonnet-20241022")

# Ollama (本地模型)
from autogen_ext.models.ollama import OllamaChatCompletionClient

client = OllamaChatCompletionClient(model="llama3.2")

# Google Gemini
from autogen_ext.models.gemini import GeminiChatCompletionClient

client = GeminiChatCompletionClient(model="gemini-1.5-pro")
```

---

## 7. 程式碼執行

### 7.1 本地執行器

```python
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_agentchat.agents import CodeExecutorAgent

# 建立執行器
executor = LocalCommandLineCodeExecutor(
    work_dir="./workspace",
    timeout=60,  # 秒
)

# 建立代碼執行代理
code_agent = CodeExecutorAgent(
    name="code_executor",
    code_executor=executor,
)
```

### 7.2 Docker 執行器 (安全隔離)

```python
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

executor = DockerCommandLineCodeExecutor(
    image="python:3.11-slim",
    work_dir="./workspace",
    timeout=120,
)
```

### 7.3 Jupyter 執行器

```python
from autogen_ext.code_executors.jupyter import JupyterCodeExecutor

executor = JupyterCodeExecutor(
    kernel_name="python3",
    timeout=120,
)
```

---

## 8. MCP 整合 (Model Context Protocol)

### 8.1 使用 MCP 工具

```python
from autogen_ext.tools.mcp import MCPToolAdapter, StdioServerParams

# 連接 MCP 伺服器 (例如 Playwright)
mcp_params = StdioServerParams(
    command="npx",
    args=["-y", "@anthropic/mcp-server-playwright"],
)

# 建立工具適配器
async with MCPToolAdapter.from_server_params(mcp_params) as tools:
    agent = AssistantAgent(
        name="web_agent",
        model_client=model_client,
        tools=tools,
        system_message="You can browse the web using Playwright.",
    )
    await agent.run(task="Go to google.com and search for AutoGen")
```

---

## 9. 訊息類型

### 9.1 常用訊息類型

```python
from autogen_agentchat.messages import (
    TextMessage,           # 純文字訊息
    MultiModalMessage,     # 多模態 (文字 + 圖片)
    ToolCallMessage,       # 工具呼叫
    ToolCallResultMessage, # 工具結果
    StopMessage,           # 停止訊息
    HandoffMessage,        # 交接訊息
)
```

### 9.2 處理訊息

```python
async def process_result(result):
    for message in result.messages:
        if isinstance(message, TextMessage):
            print(f"[{message.source}]: {message.content}")
        elif isinstance(message, ToolCallMessage):
            print(f"Tool call: {message.content}")
```

---

## 10. 進階模式

### 10.1 嵌套團隊

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_ext.agents import AgentTool

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 內部團隊 1: 研究團隊
    researcher = AssistantAgent("researcher", model_client=model_client)
    analyst = AssistantAgent("analyst", model_client=model_client)
    research_team = RoundRobinGroupChat([researcher, analyst])

    # 內部團隊 2: 寫作團隊
    writer = AssistantAgent("writer", model_client=model_client)
    editor = AssistantAgent("editor", model_client=model_client)
    writing_team = RoundRobinGroupChat([writer, editor])

    # 將團隊包裝成工具
    research_tool = AgentTool(agent=research_team, name="research_team")
    writing_tool = AgentTool(agent=writing_team, name="writing_team")

    # 主要協調代理
    coordinator = AssistantAgent(
        name="coordinator",
        model_client=model_client,
        tools=[research_tool, writing_tool],
        system_message="You coordinate tasks between research and writing teams.",
    )

    await coordinator.run(task="Create a report about AI trends")
```

### 10.2 人機協作 (Human-in-the-Loop)

```python
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # AI 代理
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        handoffs=["user"],  # 可交接給用戶
    )

    # 用戶代理 (等待人類輸入)
    user = UserProxyAgent(name="user")

    team = RoundRobinGroupChat([assistant, user])

    # 執行時會提示用戶輸入
    await team.run(task="Let's plan a vacation together.")
```

### 10.3 狀態持久化

```python
import json
from autogen_agentchat.teams import RoundRobinGroupChat

# 保存狀態
team = RoundRobinGroupChat([agent1, agent2])
result = await team.run(task="Some task")
state = team.save_state()

with open("team_state.json", "w") as f:
    json.dump(state, f)

# 恢復狀態
with open("team_state.json", "r") as f:
    state = json.load(f)

team = RoundRobinGroupChat([agent1, agent2])
team.load_state(state)
```

---

## 11. 最佳實踐

### ✅ 正確做法

1. **使用 async/await**
   ```python
   # 好
   async def main():
       result = await agent.run(task="...")

   asyncio.run(main())
   ```

2. **設定合理的終止條件**
   ```python
   # 好 - 多重終止條件
   termination = (
       MaxMessageTermination(10) |
       TextMentionTermination("DONE") |
       HandoffTermination("user")
   )
   ```

3. **使用 Console 進行除錯**
   ```python
   from autogen_agentchat.ui import Console
   await Console(team.run_stream(task="..."))
   ```

4. **明確的系統提示詞**
   ```python
   system_message="""You are a data analyst.
   - Analyze provided data
   - Create visualizations when helpful
   - Say DONE when analysis is complete"""
   ```

5. **工具函數有清楚的 docstring**
   ```python
   async def search(query: str) -> str:
       """Search the web for information.

       Args:
           query: The search query string.

       Returns:
           Search results as a string.
       """
       ...
   ```

### ❌ 避免做法

1. **無終止條件** - 可能導致無限循環
2. **過長的對話** - 消耗大量 token
3. **同步阻塞呼叫** - 使用 async
4. **敏感資訊在代碼中** - 使用環境變數

---

## 12. 遷移指南 (AutoGen 0.2 → 新版)

### 12.1 主要變更

| 舊版 (0.2) | 新版 |
|-----------|------|
| `AssistantAgent` | `autogen_agentchat.agents.AssistantAgent` |
| `UserProxyAgent` | `autogen_agentchat.agents.UserProxyAgent` |
| `GroupChat` | `RoundRobinGroupChat` / `SelectorGroupChat` |
| `config_list` | `OpenAIChatCompletionClient` |
| 同步 API | 非同步 (async/await) |

### 12.2 程式碼對照

**舊版 (0.2):**
```python
import autogen

config_list = [{"model": "gpt-4", "api_key": "..."}]

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": config_list}
)

user_proxy = autogen.UserProxyAgent(
    name="user",
    human_input_mode="NEVER"
)

user_proxy.initiate_chat(assistant, message="Hello")
```

**新版:**
```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
    )

    result = await assistant.run(task="Hello")
    print(result)

asyncio.run(main())
```

---

## 13. 常見問題

### Q: 如何處理 API 速率限制？

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(
    model="gpt-4o",
    # 內建重試機制
    max_retries=3,
)
```

### Q: 如何取得對話歷史？

```python
result = await team.run(task="...")

for message in result.messages:
    print(f"[{message.source}]: {message.content}")

# 或使用 run_stream
async for message in team.run_stream(task="..."):
    print(message)
```

### Q: 如何設定超時？

```python
import asyncio

try:
    result = await asyncio.wait_for(
        team.run(task="..."),
        timeout=300  # 5 分鐘
    )
except asyncio.TimeoutError:
    print("Task timed out")
```

### Q: 如何使用本地模型？

```python
from autogen_ext.models.ollama import OllamaChatCompletionClient

# 確保 Ollama 正在運行
client = OllamaChatCompletionClient(
    model="llama3.2",
    host="http://localhost:11434",
)
```

---

## 14. 快速參考

### 套件安裝

| 套件 | 用途 |
|-----|------|
| `autogen-agentchat` | 高階 AgentChat API |
| `autogen-core` | 核心框架 |
| `autogen-ext[openai]` | OpenAI 整合 |
| `autogen-ext[azure]` | Azure 整合 |
| `autogen-ext[docker]` | Docker 程式碼執行 |
| `autogenstudio` | 無程式碼 GUI |

### 常用匯入

```python
# 代理
from autogen_agentchat.agents import (
    AssistantAgent,
    UserProxyAgent,
    CodeExecutorAgent,
)

# 團隊
from autogen_agentchat.teams import (
    RoundRobinGroupChat,
    SelectorGroupChat,
    Swarm,
    MagenticOneGroupChat,
)

# 終止條件
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
    HandoffTermination,
)

# UI
from autogen_agentchat.ui import Console

# 模型客戶端
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# 程式碼執行
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
```

---

## 15. 資源

### 官方資源
- [官方文件](https://microsoft.github.io/autogen/stable/)
- [GitHub](https://github.com/microsoft/autogen)
- [AutoGen Studio](https://microsoft.github.io/autogen/stable/user-guide/autogenstudio-user-guide/index.html)
- [Discord 社群](https://discord.gg/pAbnFJrkgZ)

### 相關技術
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)

### 教學資源
- [DataCamp AutoGen Tutorial](https://www.datacamp.com/tutorial/autogen-tutorial)
- [Codecademy AutoGen Guide](https://www.codecademy.com/article/autogen-tutorial-build-ai-agents)

---

*Source: [AutoGen Documentation](https://microsoft.github.io/autogen/stable/) & [GitHub Repository](https://github.com/microsoft/autogen)*
