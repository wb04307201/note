<!--module:
  parent: ai
  slug: ai/agent-architecture/framework-source-comparison
  type: article
  category: 主模块子文章
  summary: 6 大 Agent 框架源码级对比（LangGraph/AutoGPT/MetaGPT/ChatDev/CrewAI/AutoGen）+ LangGraph Supervisor 完整可运行示例 + 手搓 vs 框架决策（抽象税 4 层 + 7 信号决策树 + 5 大手搓开源项目学习地图）+ 生产建议清单。
  depth: ⭐⭐⭐⭐⭐
  status: active
-->

# Agent 框架源码对比与手搓 vs 框架决策

← [返回: Agent 架构全景](README.md)

> 架构形态（DAG / ReAct / Multi-Agent，见 [多 Agent 模式](multi-agent-patterns.md)）和通信协议（见 [通信协议与演进史](communication-protocols.md)）选定后，最后一个决策是**实现载体**：用 LangChain/CrewAI 这类框架搭，还是直接调 LLM API 手写 Agent 循环。本文先做 6 大框架源码级对比，再给出手搓 vs 框架的可量化决策。

---

## 一、核心源码对比（6 大框架）

### 1.1 LangGraph（LangChain 团队）

**核心抽象**：`StateGraph` + `Node` + `Edge` + `State` + `Checkpointer`

**架构特点**：
- 基于 DAG（可扩展为循环）
- 强类型 State（TypedDict / Pydantic）
- **Checkpointer 持久化**（PostgreSQL / Redis / SQLite）
- Human-in-the-loop 原生支持（`interrupt_before` / `interrupt_after`）
- Time Travel 调试（重放历史状态）
- **预制多 Agent 模式**：Supervisor 模式（`langgraph-supervisor` 包）+ Swarm 模式（`langgraph-swarm` 包，2025 新增）

**核心源码简化**（`langgraph/graph/state.py`）：

```python
class StateGraph:
    def __init__(self, state_schema):
        self.nodes = {}
        self.edges = {}
        self.state_schema = state_schema
        self.branches = {}  # 条件边
    
    def add_node(self, name, func):
        self.nodes[name] = func
    
    def add_edge(self, from_node, to_node):
        self.edges[(from_node, to_node)] = to_node
    
    def add_conditional_edges(self, from_node, router, path_map):
        """条件边：根据 router 函数的返回值决定下一个节点"""
        self.branches[from_node] = (router, path_map)
    
    def compile(self, checkpointer=None, interrupt_before=None):
        return CompiledGraph(
            self.nodes,
            self.edges,
            self.branches,
            self.state_schema,
            checkpointer=checkpointer,
            interrupt_before=interrupt_before
        )

class CompiledGraph:
    def invoke(self, input, config=None):
        thread_id = config["configurable"]["thread_id"]
        
        # 从 Checkpointer 恢复状态
        if self.checkpointer:
            state = self.checkpointer.load(thread_id) or input
        else:
            state = input
        
        current_node = "__start__"
        while current_node != "__end__":
            # Human-in-the-loop 检查
            if self.interrupt_before and current_node in self.interrupt_before:
                state["__interrupt__"] = True
                return state
            
            # 执行节点
            func = self.nodes[current_node]
            state = func(state)
            
            # Checkpoint
            if self.checkpointer:
                self.checkpointer.save(thread_id, state)
            
            # 路由
            if current_node in self.branches:
                router, path_map = self.branches[current_node]
                current_node = path_map[router(state)]
            else:
                current_node = self.edges.get((current_node, "__end__"), "__end__")
        
        return state
```

**LangGraph Swarm 示例（handoff 预制包）**：

```python
from langgraph_swarm import create_swarm, create_handoff_tool
from langgraph.prebuilt import create_react_agent

transfer_to_sales = create_handoff_tool(
    agent_name="sales_agent",
    description="Transfer to sales for pricing/quotes.",
)
transfer_to_support = create_handoff_tool(
    agent_name="support_agent",
    description="Transfer to support for technical issues.",
)

sales_agent = create_react_agent(
    llm, tools=[transfer_to_support],
    prompt="You handle sales inquiries.",
    name="sales_agent",
)
support_agent = create_react_agent(
    llm, tools=[transfer_to_sales],
    prompt="You handle technical support.",
    name="support_agent",
)

workflow = create_swarm(
    [sales_agent, support_agent],
    default_active_agent="sales_agent",
)
app = workflow.compile()
```

**适用场景**：生产级、复杂业务、需要审计、Human-in-the-loop

### 1.2 AutoGPT

**核心抽象**：`Agent` 循环 + `Tool` 集合 + `Memory`（向量数据库）

**架构特点**：
- 经典 ReAct 循环（无显式图）
- 长期记忆（Pinecone / Milvus）
- 自我反思（Self-Criticism）

**核心循环简化**：

```python
class AutoGPTAgent:
    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.max_iterations = 50
    
    def run(self, goal: str) -> str:
        context = [{"role": "system", "content": f"Goal: {goal}"}]
        
        for i in range(self.max_iterations):
            # 思考
            thought = self.llm.think(context)
            context.append({"role": "assistant", "content": thought})
            
            # 解析行动
            action, args = self.llm.parse_action(thought)
            
            # 终止检查
            if action == "finish":
                return args["result"]
            
            # 执行工具
            observation = self.tools[action].execute(**args)
            context.append({"role": "user", "content": f"Observation: {observation}"})
            
            # 长期记忆
            self.memory.store(thought + observation)
        
        raise MaxIterationError()
```

**适用场景**：研究探索、个人助理、长期任务

### 1.3 MetaGPT

**核心抽象**：`Role` + `Action` + `Environment` + `SOP`（Standard Operating Procedures）

**架构特点**：
- 模拟软件公司（SOP 流程）
- 角色分工明确（Architect / PM / Engineer / QA）
- Message 机制（Agent 之间通过 Message 通信）

**核心源码简化**：

```python
class Role:
    def __init__(self, name: str, profile: str, actions: List[Action]):
        self.name = name
        self.profile = profile
        self.actions = actions
        self.env: Environment = None
        self.rc = RoleContext()  # 角色记忆
    
    def put_message(self, msg: Message):
        self.env.publish(msg)
    
    def react(self) -> Message:
        """主循环：从环境拉消息 → 执行动作 → 发布消息"""
        while True:
            msg = self.env.poll_message(self.name)
            if msg is None:
                break
            
            # 选择动作
            action = self.choose_action(msg)
            
            # 执行
            result = action.run(msg)
            
            # 发布结果
            self.put_message(result)
    
    def choose_action(self, msg: Message) -> Action:
        prompt = f"Profile: {self.profile}\nMessage: {msg.content}\nChoose action:"
        action_name = self.llm.choose(prompt)
        return next(a for a in self.actions if a.name == action_name)
```

**适用场景**：软件开发、流程化任务、模拟组织

### 1.4 ChatDev

**核心抽象**：`Chat Chain` + `Role`（多个 Phase 串联）

**架构特点**：
- 模拟软件开发公司（CEO / CTO / Programmer / Reviewer / Tester）
- 多个 Phase（Design → Coding → CodeComplete → Testing）
- Chat Chain 串联每个 Phase 的多 Agent 对话

**适用场景**：中小型软件开发、教学场景

### 1.5 CrewAI

**核心抽象**：`Crew` + `Agent` + `Task` + `Process`（仓库：`github.com/crewAIInc/crewAI`）

**架构特点**：
- 强调角色协作（简单直观）
- 工具通过 Tool 抽象
- **4 种 Process**：
  - `sequential`：链式（默认，token 消耗可控）
  - `hierarchical`：有 manager agent 自动委派（token 消耗 +50%~+200%）
  - `consensual`：agent 之间协商（适合需要共识的任务）
  - `asynchronous`：并行执行（适合 I/O 密集任务）

**完整示例（Researcher + Writer + Editor）**：

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

researcher = Agent(
    role="Senior Researcher",
    goal="Uncover cutting-edge developments in {topic}",
    backstory="You are an expert research analyst...",
    tools=[search_tool, scrape_tool],
    verbose=True,
)

writer = Agent(
    role="Tech Writer",
    goal="Write a compelling article about {topic}",
    backstory="You transform complex info into readable content.",
    verbose=True,
)

editor = Agent(
    role="Editor",
    goal="Polish the article to publication quality",
    backstory="You have 20 years of editing experience.",
    verbose=True,
)

research_task = Task(
    description="Research {topic} thoroughly. Cite 5+ sources.",
    expected_output="A structured research report with sources.",
    agent=researcher,
)
write_task = Task(
    description="Write a 1500-word article based on research.",
    expected_output="A draft article with sections.",
    agent=writer,
)
edit_task = Task(
    description="Polish grammar, clarity, and flow.",
    expected_output="Final polished article.",
    agent=editor,
)

crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential,  # 或 hierarchical
    verbose=2,
)

result = crew.kickoff(inputs={"topic": "RAG evaluation"})
```

**适用场景**：内容创作、研究分析、营销文案

### 1.6 AutoGen（Microsoft）

**核心抽象**：`AssistantAgent` + `UserProxyAgent` + `GroupChat` + `GroupChatManager`（仓库：`github.com/microsoft/autogen`）

**0.2 vs 0.4 架构差异**：

| 维度 | AutoGen 0.2 | AutoGen 0.4 |
|------|-------------|-------------|
| 范式 | GroupChat（中央 manager） | Actor model（消息驱动） |
| 通信 | 函数调用 | 异步消息传递 |
| 分布式 | 单进程为主 | 原生支持分布式 actor |
| 学习曲线 | 平缓 | 较陡 |
| 适用 | 快速原型 | 生产级多 agent |

**架构特点**：
- 双 Agent 对话（Assistant + User Proxy）
- GroupChat 支持多 Agent 协作（自动选下一个发言者）
- **代码执行原生支持**（UserProxy 可执行 Python / Shell）

**双 Agent 对话示例（0.2 风格）**：

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# 1. 定义 Assistant（LLM Agent）
assistant = AssistantAgent(
    name="assistant",
    llm_config={
        "model": "gpt-4o",
        "temperature": 0
    },
    system_message="You are a helpful AI assistant."
)

# 2. 定义 User Proxy（可执行代码）
user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": True   # Docker 沙箱执行
    },
    human_input_mode="TERMINATE"  # 关键决策点请求人工
)

# 3. 双 Agent 对话
user_proxy.initiate_chat(
    assistant,
    message="Write a Python script to analyze AAPL stock prices and plot it"
)
# Assistant 生成代码 → UserProxy 执行 → 返回结果 → 循环直到满意
```

**0.4 风格（autogen-agentchat 新 API）**：

> ⚠️ 0.4 中 `initiate_chat` + `code_execution_config` 的 0.2 写法已不再适用：代码执行改由 **`CodeExecutorAgent` + `LocalCommandLineCodeExecutor`** 承载，多 Agent 会话用 **`RoundRobinGroupChat` + `await team.run(...)`**；`UserProxyAgent` 在 0.4 中仅用于人工输入（human-in-the-loop），不负责代码执行。

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o")

# 1. LLM Agent：生成代码
assistant = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="You are a helpful AI assistant. Write code to solve tasks.",
)

# 2. 代码执行 Agent（替代 0.2 的 UserProxyAgent + code_execution_config）
executor = CodeExecutorAgent(
    name="executor",
    code_executor=LocalCommandLineCodeExecutor(work_dir="coding"),
)

# 3. 组队轮流对话（0.4 的 teams 抽象）
team = RoundRobinGroupChat([assistant, executor], max_turns=10)

async def main():
    await Console(team.run_stream(task="Write a Python function to compute Fibonacci numbers."))

asyncio.run(main())
```

**GroupChat 多 Agent 模式（0.2 兼容写法）**：

> 注：以下 `GroupChat` + `GroupChatManager` 为 0.2 API（`pip install pyautogen` 的兼容包仍可用）；0.4 对应写法是上例的 `RoundRobinGroupChat`（可换 `SelectorGroupChat` 实现"由 LLM 选下一个发言者"）。

```python
# 0.2 兼容：多个 Assistant + 一个 GroupChat Manager
planner = AssistantAgent("planner", llm_config=...)
coder = AssistantAgent("coder", llm_config=...)
reviewer = AssistantAgent("reviewer", llm_config=...)

groupchat = GroupChat(
    agents=[user_proxy, planner, coder, reviewer],
    messages=[],
    max_round=20
)
manager = GroupChatManager(groupchat=groupchat, llm_config=...)

user_proxy.initiate_chat(
    manager,
    message="Build a web scraper for news articles"
)
```

**适用场景**：代码生成、需要 Human-in-the-loop、多 Agent 协作

### 1.7 6 大框架对比表

| 框架 | 抽象 | 多 Agent | 代码执行 | 可观测 | 学习曲线 | 适用场景 |
|------|------|---------|---------|--------|---------|---------|
| **LangGraph** | Graph + State | 中（需手写） | 弱 | 强（Studio） | 陡 | 生产级、复杂业务 |
| **AutoGPT** | Loop + Memory | 弱 | 中 | 弱 | 平 | 研究探索 |
| **MetaGPT** | Role + SOP | 强（Pseudo-org） | 中 | 中 | 中 | 软件开发 |
| **ChatDev** | Chat Chain | 中（Phase 内） | 弱 | 弱 | 平 | 中小软件、教学 |
| **CrewAI** | Crew + Process | 强（声明式） | 弱 | 中 | 平 | 内容创作、营销 |
| **AutoGen** | Assistant + Proxy | 强（GroupChat） | 强 | 中 | 中 | 代码生成、HITL |

> LangGraph 的「多 Agent：中（需手写）」是 2024 年口径；2025 年新增 `langgraph-supervisor` / `langgraph-swarm` 预制包后多 Agent 能力显著增强（见 §1.1），但图编排本体仍需手写。

---

## 二、LangGraph Supervisor 完整可运行示例

> 手搓版 Supervisor（不依赖预制包，展示 LLM 决策路由 + Checkpointer + Human-in-the-loop + Time Travel 全链路）。模式原理见 [多 Agent 模式 §1.1](multi-agent-patterns.md)。

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage

# 1. 定义 State（强类型）
class AgentState(TypedDict):
    messages: Annotated[list, "对话历史"]
    next_agent: str
    task_completed: bool

# 2. 定义 Worker Agents
def create_researcher():
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    return create_react_agent(
        llm,
        tools=[search_tool, wikipedia_tool],
        prompt="你是一名研究员，专注于网络检索和事实核实。"
    )

def create_writer():
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    return create_react_agent(
        llm,
        tools=[],
        prompt="你是一名内容撰写员，擅长将研究结果组织成结构化文档。"
    )

# 3. 定义 Supervisor
def supervisor(state: AgentState) -> AgentState:
    """Supervisor 决策下一个 Agent"""
    prompt = f"""根据当前对话决定下一个 Agent：
    - researcher：当需要事实检索时调用
    - writer：当需要撰写内容时调用
    - FINISH：当任务完成时调用
    
    对话历史：
    {state['messages']}
    
    决策（researcher / writer / FINISH）："""
    
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    decision = llm.invoke(prompt).content.strip().lower()
    
    if "finish" in decision:
        return {**state, "next_agent": "FINISH", "task_completed": True}
    
    return {**state, "next_agent": decision}

# 4. 定义路由
def route(state: AgentState) -> Literal["researcher", "writer", "__end__"]:
    if state["task_completed"]:
        return "__end__"
    return state["next_agent"]

# 5. 构建 Graph
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("supervisor", supervisor)
workflow.add_node("researcher", create_researcher())
workflow.add_node("writer", create_writer())

# 添加边
workflow.add_edge(START, "supervisor")

# Supervisor → 条件路由
workflow.add_conditional_edges(
    "supervisor",
    route,
    {
        "researcher": "researcher",
        "writer": "writer",
        "__end__": END
    }
)

# Worker → 回到 Supervisor
workflow.add_edge("researcher", "supervisor")
workflow.add_edge("writer", "supervisor")

# 6. 编译（带 Checkpointer + Human-in-the-loop）
memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["writer"]   # Writer 前暂停（关键决策人工确认）
)

# 7. 运行
config = {"configurable": {"thread_id": "1"}}
result = app.invoke(
    {"messages": [HumanMessage(content="研究 AI 趋势并撰写综述")]},
    config=config
)
print(result["messages"][-1].content)

# 8. Time Travel（重放历史状态）
history = app.get_state_history(config)
for state in history:
    print(f"Step: {state.values}")
```

### 2.1 手搓 Supervisor 简化实现（框架无关）

不依赖 LangGraph 的最小 Supervisor 骨架（理解预制包内部逻辑用）：

```python
class Supervisor:
    def __init__(self, workers: dict):
        self.workers = workers
        self.history = []

    async def dispatch(self, task: str) -> str:
        plan = await self.plan(task)
        results = []
        for step in plan["steps"]:
            worker_name = step["worker"]
            input_data = step["input"]
            result = await self.workers[worker_name].run(input_data)
            results.append(result)
            self.history.append({"step": worker_name, "result": result})
        return self.synthesize(results)

    async def plan(self, task: str) -> dict:
        # 用 LLM 拆解任务
        prompt = f"Break down: {task}\nReturn JSON: {{'steps': [...]}}"
        return await llm.agenerate(prompt)
```

---

## 三、手搓 vs 框架：抽象税与决策权（🆕 2026-10）

> 定位：[多 Agent 模式 · 决策树](multi-agent-patterns.md)解决的是**架构形态**问题（DAG / ReAct / Plan / Multi-Agent）；本节解决的是**实现载体**问题——同一套架构，用 LangChain/CrewAI 这类框架搭，还是直接调 LLM API 手写 Agent 循环。面试题版（三问检验 + 30 秒话术）见 §3.8 交叉引用。

### 3.1 核心命题：「框架太重」是现象不是理由

"LangChain 太重了" 是社区高频抱怨，但**重是现象，不是决策依据**。只说"重"等于没做架构决策。给出三问检验框架：

| # | 问题 | 指向 |
|---|------|------|
| 1 | **重在哪？** | 抽象税的量化拆解（→ §3.2，4 层） |
| 2 | **代价是什么？** | 分层归因：性能 / 可观测 / 版本 / 安全（→ §3.5 对照表） |
| 3 | **怎么权衡？** | 场景化决策，7 信号任 2 命中即手搓（→ §3.6 决策树） |

> 反直觉：手搓的动机不是"框架不好"，而是**决策权归属**——当你的业务核心价值就藏在 Agent 循环的每个中间状态里时，把循环交给框架等于把核心决策权外包。

### 3.2 抽象税 4 层拆解（重在哪）

| 层 | 表现 | 量化方式 |
|----|------|---------|
| **L1 调用栈** | 一次简单文本生成要穿 Chain → LLMChain → BaseChain → BaseLLM → BaseOpenAI → OpenAI 等多层类 | 调用栈深度约 5×（对比裸 SDK 直调 1 层） |
| **L2 版本变动** | 业务没变代码跟着改：Chain API → LCEL，`create_react_agent` → `create_agent` | 升级成本（框架大版本≈一次全量回归测试） |
| **L3 黑盒可观测** | 框架隐藏了拼给你的原始提示词，出问题时日志里看到的是框架中间对象而非真实 prompt | 调试成本（定位一次问题的时间 ×2~×3） |
| **L4 冗余提示词** | 通用封装为覆盖各种场景夹带的模板提示词，破坏前缀对齐 → **Prompt Caching 频繁失效** | token 成本（缓存命中率下降直接换算成钱） |

**L4 是最容易被忽略的一层**：前缀缓存按"相同前缀命中"计费打折，框架封装层每次拼 prompt 的顺序/模板差异都会打断前缀对齐——抽象税最终以 token 账单的形式结算。

### 3.3 权威佐证

- **Anthropic 官方（«Building Effective Agents» 2024-12）**：框架为了通用性需要额外抽象层，会**隐藏最初的提示词**，使调试更困难；建议大多数场景直接调用 API，从简单模式（Workflow）开始，只在确实需要 Agent 灵活性时才引入框架抽象。案例深读见 [多 Agent 模式 · 生产案例](multi-agent-patterns.md)。
- **Octomind 真实弃用案例**：用 LangChain 一年多后弃用改手搓——触发点是**需要在 Agent 运行中动态调整可用工具集**，框架没有提供观察/控制中间状态的机制，每次想介入都要先理解框架内部实现。原文：*Agent frameworks shooting themselves in the foot*（链接见文末参考资源）。

### 3.4 手搓的 3 大回报（不是从头造轮子）

手搓 ≠ 从零实现工具调用协议、重写 HTTP 客户端。**SDK 层（anthropic / openai 官方 SDK）照用**，手搓的只是中间那一层 Agent 循环（ReAct loop、上下文管理、调度策略）：

1. **ReAct 绝对掌控**：模型每步在想什么、调了什么工具、工具返回值合不合理——全部可实时插桩（interceptor）、中断、动态修正。框架下这需要先读懂框架源码再找 hook 点。
2. **上下文工程极致压缩**：手写循环才能做前缀感知与动态压缩——工具输出截断、对话历史折叠、时间维度裁剪、按需摘要（Claude Code 同款做法，详见 [coding-agents](../coding-agents/README.md)）。框架的通用 memory 组件做不到按你业务定制。
3. **流式交互与并发调度**：只读工具全量并发、写操作严格串行、超时中断秒级终止——这些调度策略天然是业务决策，不是框架能预设的。

### 3.5 代价对照表

| 维度 | 框架 | 手搓 |
|------|------|------|
| **单次执行延迟** | 约 200~500ms（封装层 + 状态转换 + Callback 机制） | 约 100ms（纯 API 直调） |
| **开发速度** | 工具调用几十分钟接好 | 自写要几天（Tool 注册 / 参数解析 / 异常处理 / 消息管理） |
| **生态** | RAG / Memory / VectorDB / Prompt 模板现成 | 全部自建 |
| **可控性** | 中间状态难干预（要读框架源码找 hook） | 每步插桩 |
| **数据安全** | Prompt 与执行记录过第三方抽象层 | 自管（合规域内闭环） |
| **适用** | 原型验证 / demo / 生态依赖重 | 生产 / 机器人 / 低延迟 / 强合规 |

> 延迟数字为量级参考（截至 2026-10 源文数据），随框架版本变化，核心是**相对关系**：框架开销主要来自封装层状态转换与 Callback 链，手搓省掉的正是这部分。

### 3.6 决策树：什么时候手搓，什么时候用框架

**7 个信号（任 2 个命中 → 手搓）**：

| # | 信号 | 典型场景 |
|---|------|---------|
| 1 | 延迟敏感 | 实时机器人 / 自动驾驶 / 高频交易 |
| 2 | 需要运行中动态调整工具集 | Octomind 场景（框架无此机制） |
| 3 | 需要每步插桩 / 中断 / 修正 | ReAct 掌控需求 |
| 4 | 上下文成本敏感 | 前缀缓存优化（L4 抽象税） |
| 5 | 数据合规 | Prompt / 执行记录不出域 |
| 6 | 业务是 Agent + Workflow 混合 | 纯 Agent 框架不合身（见 [多 Agent 模式 · 架构决策树](multi-agent-patterns.md)） |
| 7 | 已有工程团队维护能力 | 有能力养自研循环 |

**框架占优**：原型期 / 创业快速验证 / 生态依赖重（RAG 全家桶）/ 团队 AI 工程经验少。

**折中方案（生产最常见）**：**核心循环手写 + 周边工具性能力借用**——ReAct 循环、上下文管理、调度自写；tracing、文档解析、向量库 client 这些工具性能力直接用现成库。一句话：**「心脏手写，四肢借用」**。

### 3.7 5 大手搓开源项目（学习地图）

| 项目 | 星标（截至 2026-10 源文数据，约数） | 核心学习点 |
|------|------|-----------|
| [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | 约 7.5k | 约 100 行实现完整 Agent + SWE-bench 高分 — **最极简骨架**，先读它 |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | 约 30k | Agent / Runner / Tool / Guardrail / Handoff 5 概念白盒化 — **最标准范式** |
| [Aider](https://github.com/Aider-AI/aider) | 约 50k | repo map（仓库压缩成结构地图）+ diff / udiff / 全文件 3 编辑模式 — **上下文工程教科书** |
| [Goose（Block）](https://github.com/block/goose) | 约 54k | Rust 高性能 + MCP 深度集成 — **系统级并发架构** |
| [PydanticAI](https://github.com/pydantic/pydantic-ai) | 20k+ | FastAPI 式类型安全 + 依赖注入 + 结构化输出 — **生产级类型安全** |

> 学习路径建议：mini-swe-agent（看懂最小循环）→ OpenAI Agents SDK（看懂标准抽象）→ Aider（看懂上下文工程）→ Goose/PydanticAI（看懂生产化）。

### 3.8 交叉引用

- 面试题版（双层互链）：[12.interview/11.ai/handcraft-vs-framework](../../../12.interview/11.ai/handcraft-vs-framework/README.md) — 三问检验 + 30 秒话术 + 反直觉陷阱
- 本目录内部：§一（6 大框架源码对比）、[多 Agent 模式 · Anthropic «Building Effective Agents» 案例](multi-agent-patterns.md)（手搓论的权威出处）、[多 Agent 模式 · 决策树](multi-agent-patterns.md)（架构形态决策，与本节实现载体决策互补）
- 关联：[coding-agents](../coding-agents/README.md) — Claude Code / Codex / OpenCode / OMP 成品 Agent 横向对比（手搓范式的工业级实证）

---

## 四、反直觉：CrewAI Process 选择不是无关紧要

**真相**：`sequential` vs `hierarchical` 在 token 消耗上**可差 3x**。

- `sequential`：每步 token 可预算，总量 = Σ(每步 token)
- `hierarchical`：manager agent 每步决策，叠加 manager LLM 调用，总量 = Σ(每步 token × manager 倍率)
- `consensual`：agent 间投票，token × agent 数

→ **建议**：先用 `sequential` 跑通，按需升级 `hierarchical`（仅在需要动态委派时）。

---

## 五、生产建议清单

| 建议 | 优先级 | 说明 |
|------|--------|------|
| **能用 Workflow 不用 Agent** | P0 | 成本可预测、稳定 |
| **多 Agent 必须有清晰角色** | P0 | 避免通信混乱 |
| **Checkpointer 必须启用** | P0 | 状态可恢复、Time Travel |
| **监控 Token 消耗** | P1 | 成本控制（>30% 多 Agent 占比要警惕） |
| **Trace 工具完整** | P1 | 调试能力（Langfuse / LangSmith） |
| **熔断机制** | P1 | Agent 失败时的兜底（类比 Circuit Breaker） |
| **Supervisor 备份** | P1 | 避免单点故障（Multi-Master） |
| **A2A 协议探索** | P2 | 未来趋势（2026+ 主流） |
| **Container 沙箱** | P2 | 代码执行安全（Docker 隔离） |
| **Human Review 点** | P2 | 关键决策人工确认（interrupt_before） |

---

## 相关章节

- 上游综述：[Agent 架构全景](README.md) — 单 Agent 架构选型 + 面试速查
- 姊妹篇：[多 Agent 架构模式与选型](multi-agent-patterns.md) — 架构形态决策（本文实现载体决策的上游）
- 姊妹篇：[通信协议与演进史](communication-protocols.md) — A2A / MCP 协议层
- 平台层对比：[ai-platforms](../ai-platforms/README.md) — Coze / Dify / LangGraph 低代码平台横向对比
- 面试题版：[12.interview/11.ai/handcraft-vs-framework](../../../12.interview/11.ai/handcraft-vs-framework/README.md)

## 参考资源

### 论文

- **MetaGPT**：Hong et al., 2023, "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework"
- **AutoGen**：Wu et al., 2023, "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"

### 框架文档

- **LangGraph**：https://langchain-ai.github.io/langgraph/
- **CrewAI**：https://docs.crewai.com/
- **AutoGen**：https://microsoft.github.io/autogen/
- **MetaGPT**：https://docs.deepwisdom.ai/

### 博客与指南

- **Anthropic "Building Effective Agents"**：https://www.anthropic.com/research/building-effective-agents
- **Octomind "Agent frameworks shooting themselves in the foot"**（§3.3 弃用案例出处）：https://www.octomind.dev/blog/agent-frameworks-shooting-themselves-in-the-foot
- **二哥 Java 进阶之路·手搓 Agent**（§三 源文）：https://javabetter.cn/ai/video/why-handcraft-agent-not-framework.html

---

← [返回: Agent 架构全景](README.md)
