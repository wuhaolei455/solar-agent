"""Demo 02: LCEL Chain

使用 LangChain LCEL 表达式构建一个简单的 Prompt → Model → Parser 链。
根据主题生成英语段落并列出词汇。
"""

import sys
import os
from pathlib import Path

from langchain.chat_models import init_chat_model

# 将项目根目录加入 sys.path，以便导入 shared 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import load_env
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# 加载环境变量
load_env()

assert os.getenv("OPENAI_API_KEY"), "请先配置 OPENAI_API_KEY"

prompt = PromptTemplate.from_template(
    "Write an English paragraph about {topic} and list 3 vocabulary words."
)
model = init_chat_model(
    "openai:gpt-5.2",
    temperature=0
)
output_parser = StrOutputParser()

# 使用 LCEL 表达式将 prompt、model、parser 串联起来
chain = prompt | model | output_parser

result = chain.invoke({"topic": "climate change"})
print(result)
