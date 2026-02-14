import os
import time
from shared import setup

import gradio as gr
import whisper
import edge_tts
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

setup()

# 加载 Whisper 语音识别模型
asr_model = whisper.load_model("turbo")

# 存储不同用户的记忆
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

model = init_chat_model(
    "openai:gpt-5.2",
    temperature=0
)
output_parser = StrOutputParser()

chain = english_tutor_prompt | model | output_parser
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="user_message",
    history_messages_key="chat_history",
)


def speech_to_text(audio_path: str) -> str:
    """把用户语音转成文本（Whisper ASR）"""
    transcribed = asr_model.transcribe(audio_path)
    return transcribed["text"]


def text_to_speech(text: str) -> str:
    """输入文本 → 输出音频文件路径（Edge TTS）"""
    print(f"[TTS] Processing: {text}")
    audio_path = f"./output_{int(time.time())}.mp3"
    communicate = edge_tts.Communicate(text, "en-GB-SoniaNeural")
    with open(audio_path, "wb") as file:
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
    return audio_path


def stream_ai_response(user_message: str, session_id: str):
    """流式调用大模型，逐 chunk 生成回复"""
    partial_answer = ""
    for chunk in chain_with_history.stream(
        {"user_message": user_message},
        config={"configurable": {"session_id": session_id}}
    ):
        if chunk:
            partial_answer += chunk
            yield partial_answer


def process_voice_and_stream(audio_path: str, history: list):
    """
    语音交互主流程：
    1. 语音识别 → 文本
    2. 流式调用 LLM → 文字回复
    3. 文字转语音 → 音频回复
    """
    user_text = speech_to_text(audio_path)
    if not user_text:
        yield history, None
        return

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": ""})
    yield history, None

    session_id = "user_001"

    full_response = ""
    for partial in stream_ai_response(user_text, session_id):
        full_response = partial
        history[-1]["content"] = full_response
        yield history, None

    audio_reply = text_to_speech(full_response)
    yield history, audio_reply


with gr.Blocks(theme=gr.themes.Soft()) as chat_ui:
    gr.Markdown("# 🎙️ 流式多模态英语助手")

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="请开口说英语 (Speak English)"
            )
            audio_output = gr.Audio(label="AI 语音回复", autoplay=True)

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="对话记录")
            clear_btn = gr.Button("清空对话")

    # 当录音结束时触发
    audio_input.stop_recording(
        fn=process_voice_and_stream,
        inputs=[audio_input, chatbot],
        outputs=[chatbot, audio_output]
    )

    clear_btn.click(lambda: [], None, chatbot)


if __name__ == "__main__":
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7870, share=False)
