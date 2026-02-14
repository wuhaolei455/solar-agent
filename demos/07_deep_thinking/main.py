from typing import Mapping, Any, cast
from langchain_core.messages import AIMessageChunk, BaseMessageChunk
from langchain_openai.chat_models import base

_original_convert = base._convert_delta_to_message_chunk


def _patched_convert(
    _dict: Mapping[str, Any], default_class: type[BaseMessageChunk]
) -> BaseMessageChunk:
    chunk = _original_convert(_dict, default_class)
    try:
        role = cast(str, _dict.get("role"))
        if _dict.get("reasoning_content") and (
            role == "assistant" or default_class == AIMessageChunk
        ):
            chunk.additional_kwargs["reasoning_content"] = _dict["reasoning_content"]
    except Exception:
        pass
    return chunk


base._convert_delta_to_message_chunk = _patched_convert

########################  hook  ########################

import os
from shared import setup

import gradio as gr
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessageChunk
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

setup()

store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


english_tutor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly English tutor.

        Help the learner improve step by step.
        Keep responses short, clear, and conversational.

        When correcting:
        - First show the corrected sentence.
        - Then give a very brief reason (1–2 short sentences).
        - Use simple, everyday English.
        - Encourage the learner to try again.

        Do not give long explanations or grammar lectures.
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{user_message}"),
])


def build_chain(deep_thinking: bool):
    """根据是否开启深度思考，构建不同的 chain。

    - 普通模式：使用 .env 中配置的模型，直接回答
    - 深度思考：使用 deepseek-v3.2-think，返回思考过程 + 回答
    """
    if deep_thinking:
        print("[Deep Thinking] 已启用深度思考模式 (deepseek-v3.2-think)")
        model = init_chat_model(
            "openai:deepseek-v3.2-think",
            temperature=0.6,
        )
    else:
        model = init_chat_model(
            "openai:gpt-5.2",
            temperature=0
        )

    # 注意：不加 StrOutputParser，保留原始 AIMessageChunk 以读取 reasoning_content
    chain = english_tutor_prompt | model

    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="user_message",
        history_messages_key="chat_history",
    )


def stream_ai_response(user_message: str, session_id: str, deep_thinking: bool):
    """流式调用大模型，分离思考过程和最终回答。"""
    chain_with_history = build_chain(deep_thinking)

    thinking_buffer = ""
    answer_buffer = ""

    for chunk in chain_with_history.stream(
        {"user_message": user_message},
        config={"configurable": {"session_id": session_id}}
    ):
        if not isinstance(chunk, AIMessageChunk):
            continue

        # 思考过程（仅展示，不存入对话记忆）
        if "reasoning_content" in chunk.additional_kwargs:
            thinking_buffer += chunk.additional_kwargs["reasoning_content"]

        # 最终回答（自动存入对话记忆）
        if chunk.content:
            answer_buffer += chunk.content

        # 组装输出：有思考时显示思考块，始终显示回答
        if thinking_buffer:
            yield f"<details><summary>💭 思考过程</summary>\n\n{thinking_buffer}\n\n</details>\n\n{answer_buffer}"
        else:
            yield answer_buffer


def chat_handler(message: str, history: list, deep_thinking: bool):
    session_id = "user_001"
    for partial in stream_ai_response(message, session_id, deep_thinking):
        yield partial


chat_ui = gr.ChatInterface(
    fn=chat_handler,
    additional_inputs=[
        gr.Checkbox(label="🧠 深度思考", value=False)
    ],
    title="英语学习助手（深度思考版）",
    description="支持普通模式 / 深度思考模式的英语学习助手。勾选「深度思考」可查看模型的推理过程。"
)


if __name__ == "__main__":
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7880, share=False)
