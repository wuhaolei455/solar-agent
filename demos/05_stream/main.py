import os
from shared import setup

import gradio as gr
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

setup()


store = {}

def get_session_history(session_id: str) -> list:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

model = init_chat_model(
    "openai:gpt-5.2",
    temperature=0
)

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
    MessagesPlaceholder(variable_name="chat_history"), # 记忆存放处
    ("human", "{user_message}")
])

output_parser = StrOutputParser()

chain = english_tutor_prompt | model | output_parser
chain_with_history = RunnableWithMessageHistory(
    chain, 
    get_session_history,
    input_messages_key="user_message",
    history_messages_key="chat_history"
)


def stream_ai_response(user_message: str, session_id: str) -> str:
    partial_answer = ""
    response = chain_with_history.stream(
        {"user_message": user_message},
        config={"configurable": {"session_id": session_id}}
    )
    for chunk in response:
        if chunk:
            partial_answer += chunk
            yield partial_answer


def chat_handler(message: str, history: list) -> str:
    session_id = "user_001"
    for partial in stream_ai_response(message, session_id):
        yield partial


chat_ui = gr.ChatInterface(
    fn=chat_handler,
    title="英语学习助手",
    description="一个基于 LLM 的对话式英语学习助手示例"
)


if __name__ == "__main__":
    # 避免代理拦截 localhost 请求导致 403
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7860, share=False)
