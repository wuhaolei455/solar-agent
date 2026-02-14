"""Demo 01: 天气预报 Agent

使用 LangChain Agent 构建一个带双关语风格的天气预报助手。
支持工具调用、上下文传递、结构化输出和对话记忆。
"""

import sys
from dataclasses import dataclass
from pathlib import Path

# 将项目根目录加入 sys.path，以便导入 shared 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import load_env
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver


# 加载环境变量
load_env()


# 定义系统提示
SYSTEM_PROMPT = """你是一位擅长用双关语表达的专家天气预报员。

你可以使用两个工具：

- get_weather_for_location：用于获取特定地点的天气
- get_user_location：用于获取用户的位置

如果用户询问天气，请确保你知道具体位置。如果从问题中可以判断他们指的是自己所在的位置，请使用 get_user_location 工具来查找他们的位置。"""

# 定义上下文模式
@dataclass
class Context:
    """自定义运行时上下文模式。"""
    user_id: str

# 定义工具
@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取用户信息。"""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"

# 配置模型
model = init_chat_model(
    "openai:gpt-5.2",
    temperature=0
)

# 定义响应格式
@dataclass
class ResponseFormat:
    """代理的响应模式。"""
    # 带双关语的回应（始终必需）
    punny_response: str
    # 天气的任何有趣信息（如果有）
    weather_conditions: str | None = None

# 设置记忆
checkpointer = InMemorySaver()

# 创建代理
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# 运行代理
# `thread_id` 是给定对话的唯一标识符。
config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "佛罗里达天气怎么样？现在的气温是多少"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])

# 注意，我们可以使用相同的 `thread_id` 继续对话。
response = agent.invoke(
    {"messages": [{"role": "user", "content": "谢谢！"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
