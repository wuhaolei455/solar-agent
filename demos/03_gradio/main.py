import os
from shared import setup

import gradio as gr
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

setup()

model = init_chat_model(
    "openai:gpt-5.2",
    temperature=0
)


def get_ai_response(user_message: str, chat_history: list) -> str:
    """
    调用大模型，生成回复内容
    - user_message: 当前用户输入
    - chat_history: 过往对话历史（可用于上下文）
    """

    english_tutor_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an English Learning Assistant.

            Your primary role is to help learners improve their English through:
            - clear explanations
            - gentle corrections
            - practical examples
            - guided practice

            Follow these principles at all times:
            1. Be encouraging and patient. Never criticize the learner.
            2. Correct mistakes politely and explain why they are wrong.
            3. Use simple, clear language unless the learner asks for advanced explanations.
            4. Always prefer examples over abstract rules.
            5. Adapt your response to the learner's English level when possible.

            When responding:
            - If the learner makes a mistake, first show the corrected version.
            - Then explain the correction briefly.
            - Then provide 1–2 example sentences.
            - If appropriate, ask a short follow-up question to encourage practice.
            """.strip()
        ),
        ("human", "{user_message}")
    ])

    output_parser = StrOutputParser()

    chain = english_tutor_prompt | model | output_parser
    result = chain.invoke({"user_message": user_message})
    return result


def chat_handler(message: str, history: list) -> str:
    return get_ai_response(message, history)


chat_ui = gr.ChatInterface(
    fn=chat_handler,
    title="英语学习助手",
    description="一个基于 LLM 的对话式英语学习助手示例"
)


if __name__ == "__main__":
    # 避免代理拦截 localhost 请求导致 403
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7860, share=False)
