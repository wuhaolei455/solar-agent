from shared import setup
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

setup()

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
