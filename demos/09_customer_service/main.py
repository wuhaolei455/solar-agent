"""
Demo 09: 智能客服系统 (Customer Service System)

多 Agent 协作架构：Router + Handoff + Human-in-the-loop
- Router Agent: 识别用户意图，路由到专业 Agent
- FAQ Agent: 基于 RAG 知识库回答常见问题
- Order Agent: 查询订单状态、物流信息（Tool Use）
- Tech Support Agent: 多轮技术诊断（ReAct）
- Complaint Agent: 处理投诉，支持 Human-in-the-loop 升级
- Chitchat Agent: 闲聊兜底
- QA Inspector: 质检回复质量，敏感词过滤

图结构：
  START → router → [faq / order / tech_support / complaint / chitchat]
                      ↓
                   qa_inspector → END (or escalate_to_human)
"""

import os
import json
from typing import TypedDict, Annotated, Literal
from shared import setup

import gradio as gr
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

setup()

# ======================== 全局模型 ========================

llm = init_chat_model("openai:gpt-5.2", temperature=0)


# ======================== State 定义 ========================

class CustomerServiceState(TypedDict):
    user_message: str              # 用户输入
    intent: str                    # 识别出的意图
    response: str                  # Agent 的回复
    qa_result: str                 # 质检结果
    qa_passed: bool                # 是否通过质检
    escalated: bool                # 是否升级人工
    debug_info: list[str]          # 调试信息（节点流转日志）


# ======================== 模拟知识库和数据 ========================

# FAQ 知识库（实际项目中可使用向量数据库 RAG）
FAQ_KNOWLEDGE_BASE = {
    "退货": "退货政策：收到商品7天内可无理由退货，需保持商品完好。请在【我的订单】中点击【申请退货】，上传凭证即可。",
    "换货": "换货说明：商品质量问题可在15天内申请换货。请联系在线客服提供订单号和照片，我们将尽快处理。",
    "发票": "发票获取：订单完成后，可在【我的订单】-【发票】中下载电子发票。如需纸质发票，请在下单时备注。",
    "优惠券": "优惠券使用：优惠券可在结算时自动抵扣，部分优惠券有使用门槛（如满199减50）。已过期优惠券无法使用。",
    "会员": "会员权益：会员享受专属折扣、生日礼金、优先客服等特权。年费会员另享免运费服务。",
    "运费": "运费说明：订单满99元包邮，部分偏远地区除外。未满免邮门槛，运费根据地区收取5-15元。",
}


# 订单数据库（模拟）
ORDER_DATABASE = {
    "12345": {
        "status": "已发货",
        "tracking": "SF1234567890",
        "items": ["无线耳机 x1", "手机壳 x2"],
        "total": 299.0,
        "estimated_delivery": "2026-02-18"
    },
    "67890": {
        "status": "配送中",
        "tracking": "YT9876543210",
        "items": ["运动手表 x1"],
        "total": 799.0,
        "estimated_delivery": "2026-02-16"
    },
}


# ======================== 工具函数 ========================

@tool
def search_faq(query: str) -> str:
    """搜索 FAQ 知识库。输入用户问题关键词，返回相关答案。"""
    # 简单关键词匹配（实际项目中应使用向量相似度搜索）
    for keyword, answer in FAQ_KNOWLEDGE_BASE.items():
        if keyword in query:
            return f"【FAQ】{answer}"
    return "【FAQ】抱歉，暂未找到相关答案。您可以详细描述问题，我将为您人工解答。"


@tool
def query_order(order_id: str) -> str:
    """查询订单状态和物流信息。输入订单号，返回订单详情。"""
    order = ORDER_DATABASE.get(order_id)
    if order:
        return (
            f"【订单详情】\n"
            f"订单号：{order_id}\n"
            f"状态：{order['status']}\n"
            f"物流单号：{order['tracking']}\n"
            f"商品：{', '.join(order['items'])}\n"
            f"金额：¥{order['total']}\n"
            f"预计送达：{order['estimated_delivery']}"
        )
    return "【订单查询】未找到该订单，请确认订单号是否正确。"


@tool
def check_logistics(tracking_number: str) -> str:
    """查询物流信息。输入物流单号，返回物流轨迹。"""
    # 模拟物流查询
    if tracking_number.startswith("SF"):
        return (
            f"【物流信息】\n"
            f"单号：{tracking_number}\n"
            f"2026-02-15 10:30 [深圳转运中心] 快件已到达\n"
            f"2026-02-15 14:20 [深圳] 派送中，预计今日送达\n"
            f"2026-02-15 16:45 [深圳] 快件已签收"
        )
    elif tracking_number.startswith("YT"):
        return (
            f"【物流信息】\n"
            f"单号：{tracking_number}\n"
            f"2026-02-14 18:00 [上海仓库] 已发货\n"
            f"2026-02-15 09:15 [杭州转运中心] 运输中\n"
            f"2026-02-16 预计送达"
        )
    return "【物流查询】未找到物流信息，请确认单号是否正确。"


@tool
def diagnose_issue(issue_description: str) -> str:
    """诊断技术问题。输入问题描述，返回诊断建议。"""
    # 简单的关键词匹配诊断（实际项目中可接入更复杂的诊断系统）
    issue_lower = issue_description.lower()

    if "无法" in issue_lower and ("登录" in issue_lower or "登陆" in issue_lower):
        return "【诊断建议】请尝试：1) 确认账号密码是否正确 2) 清除浏览器缓存 3) 重置密码 4) 更换网络环境"
    elif "闪退" in issue_lower or "崩溃" in issue_lower:
        return "【诊断建议】请尝试：1) 更新到最新版本 2) 清理应用缓存 3) 卸载重装 4) 检查系统版本兼容性"
    elif "慢" in issue_lower or "卡顿" in issue_lower:
        return "【诊断建议】请尝试：1) 关闭后台应用 2) 清理存储空间 3) 检查网络连接 4) 重启设备"
    else:
        return "【诊断建议】请提供更详细的问题描述，包括：1) 具体错误提示 2) 操作步骤 3) 设备型号和系统版本"


# ======================== Agent 节点 ========================

def router_node(state: CustomerServiceState) -> dict:
    """Router Agent: 识别用户意图，路由到对应 Agent"""
    user_message = state["user_message"]

    response = llm.invoke([
        SystemMessage(content="""你是一位智能客服路由助手，负责识别用户意图并分类。

请将用户消息分类为以下类别之一：
1. "faq" - 常见问题（退货、换货、发票、优惠券、会员、运费等）
2. "order" - 订单查询（订单状态、物流查询）
3. "tech_support" - 技术支持（登录问题、闪退、卡顿等技术故障）
4. "complaint" - 投诉建议（服务质量差、商品问题等负面反馈）
5. "chitchat" - 闲聊寒暄（问候、闲聊等非业务对话）

只返回类别名称（英文小写），不要其他内容。"""),
        HumanMessage(content=user_message)
    ])

    intent = response.content.strip().lower()
    # 确保返回值在预期范围内
    valid_intents = ["faq", "order", "tech_support", "complaint", "chitchat"]
    if intent not in valid_intents:
        intent = "chitchat"  # 默认兜底

    return {
        "intent": intent,
        "debug_info": [f"🎯 Router 识别意图: {intent}"]
    }


def faq_agent_node(state: CustomerServiceState) -> dict:
    """FAQ Agent: 基于知识库回答常见问题"""
    user_message = state["user_message"]

    # 先尝试从知识库搜索
    faq_result = search_faq.invoke({"query": user_message})

    # 如果找到答案，直接返回；否则用 LLM 生成回复
    if "暂未找到" not in faq_result:
        response_text = faq_result
    else:
        llm_response = llm.invoke([
            SystemMessage(content="""你是专业的客服 FAQ 专员。请根据用户问题，提供清晰准确的回答。
如果问题不在知识范围内，请礼貌告知用户可以转接人工客服。"""),
            HumanMessage(content=user_message)
        ])
        response_text = llm_response.content

    return {
        "response": response_text,
        "debug_info": [f"💬 FAQ Agent 已回复"]
    }


def order_agent_node(state: CustomerServiceState) -> dict:
    """Order Agent: 处理订单查询（带工具调用）"""
    user_message = state["user_message"]

    # 创建 ReAct Agent，自动决定调用哪些工具
    order_agent = create_react_agent(
        model=llm,
        tools=[query_order, check_logistics],
        prompt=(
            "你是专业的订单查询客服。请根据用户问题，使用订单查询工具获取信息。"
            "如果用户提到订单号，优先使用 query_order 工具。"
            "如果涉及物流，使用 check_logistics 工具。"
            "回复要简洁友好，直接给出查询结果。"
        ),
    )

    result = order_agent.invoke({
        "messages": [HumanMessage(content=user_message)]
    })

    final_response = result["messages"][-1].content

    return {
        "response": final_response,
        "debug_info": [f"📦 Order Agent 已处理订单查询"]
    }


def tech_support_agent_node(state: CustomerServiceState) -> dict:
    """Tech Support Agent: 技术支持诊断（ReAct + 多轮引导）"""
    user_message = state["user_message"]

    tech_agent = create_react_agent(
        model=llm,
        tools=[diagnose_issue],
        prompt=(
            "你是专业的技术支持工程师。请根据用户描述的问题，使用诊断工具提供解决方案。"
            "如果用户描述不够详细，请引导用户提供更多信息（如设备型号、系统版本、具体报错等）。"
            "回复要专业且通俗易懂，提供分步骤的解决方案。"
        ),
    )

    result = tech_agent.invoke({
        "messages": [HumanMessage(content=user_message)]
    })

    final_response = result["messages"][-1].content

    return {
        "response": final_response,
        "debug_info": [f"🔧 Tech Support Agent 已提供技术支持"]
    }


def complaint_agent_node(state: CustomerServiceState) -> dict:
    """Complaint Agent: 处理投诉（情感分析 + 升级判断）"""
    user_message = state["user_message"]

    response = llm.invoke([
        SystemMessage(content="""你是专业的投诉处理专员。请用同理心回应用户的不满，并提供解决方案。

回复格式 JSON：
{
  "response": "向用户的回复内容（表达歉意 + 解决方案）",
  "escalate": true/false,
  "reason": "升级原因（如果需要升级）"
}

escalate 规则：
- 用户情绪非常激动、使用强烈负面词汇 → true
- 涉及金额纠纷、法律威胁 → true
- 普通抱怨、可直接处理的问题 → false

只返回 JSON，不要其他内容。"""),
        HumanMessage(content=user_message)
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        response_text = result.get("response", "非常抱歉给您带来不便，我们将尽快为您处理。")
        escalate = result.get("escalate", False)
        reason = result.get("reason", "")
    except (json.JSONDecodeError, KeyError):
        response_text = "非常抱歉给您带来不便，我们将尽快为您处理。"
        escalate = False
        reason = ""

    debug_msg = f"🚨 Complaint Agent 已处理投诉"
    if escalate:
        debug_msg += f" → 升级人工（原因：{reason}）"
        response_text += "\n\n由于您的情况较为特殊，我已为您转接人工客服，稍后将有专人为您处理。"

    return {
        "response": response_text,
        "escalated": escalate,
        "debug_info": [debug_msg]
    }


def chitchat_agent_node(state: CustomerServiceState) -> dict:
    """Chitchat Agent: 闲聊兜底"""
    user_message = state["user_message"]

    response = llm.invoke([
        SystemMessage(content="""你是友好的客服助手。请用轻松愉快的语气回应用户的闲聊或问候。
如果用户问题不明确，请引导用户描述具体需求（订单查询、技术支持、FAQ 等）。"""),
        HumanMessage(content=user_message)
    ])

    return {
        "response": response.content,
        "debug_info": [f"😊 Chitchat Agent 已回复"]
    }


def qa_inspector_node(state: CustomerServiceState) -> dict:
    """QA Inspector: 质检回复质量 + 敏感词过滤"""
    response_text = state["response"]

    # 敏感词列表（简化示例）
    sensitive_words = ["傻", "笨", "垃圾", "骗子", "滚"]

    # 检查敏感词
    has_sensitive = any(word in response_text for word in sensitive_words)

    if has_sensitive:
        qa_result = "⚠️ 质检不通过：检测到敏感词汇"
        qa_passed = False
        # 替换敏感词
        for word in sensitive_words:
            response_text = response_text.replace(word, "***")
    else:
        qa_result = "✅ 质检通过"
        qa_passed = True

    return {
        "response": response_text,  # 如果有敏感词，返回过滤后的版本
        "qa_result": qa_result,
        "qa_passed": qa_passed,
        "debug_info": [f"🔍 QA Inspector 质检: {qa_result}"]
    }


# ======================== 条件路由 ========================

def route_by_intent(state: CustomerServiceState) -> Literal["faq", "order", "tech_support", "complaint", "chitchat"]:
    """根据意图路由到对应 Agent"""
    return state["intent"]


def check_escalation(state: CustomerServiceState) -> Literal["qa_inspector", "escalate"]:
    """检查是否需要升级人工"""
    if state.get("escalated", False):
        return "escalate"
    return "qa_inspector"


# ======================== 构建 Graph ========================

def build_customer_service_graph():
    graph = StateGraph(CustomerServiceState)

    # 添加节点
    graph.add_node("router", router_node)
    graph.add_node("faq", faq_agent_node)
    graph.add_node("order", order_agent_node)
    graph.add_node("tech_support", tech_support_agent_node)
    graph.add_node("complaint", complaint_agent_node)
    graph.add_node("chitchat", chitchat_agent_node)
    graph.add_node("qa_inspector", qa_inspector_node)

    # 起始边
    graph.add_edge(START, "router")

    # Router 条件路由到各专业 Agent
    graph.add_conditional_edges("router", route_by_intent, {
        "faq": "faq",
        "order": "order",
        "tech_support": "tech_support",
        "complaint": "complaint",
        "chitchat": "chitchat",
    })

    # 各 Agent 处理后的流向
    graph.add_edge("faq", "qa_inspector")
    graph.add_edge("order", "qa_inspector")
    graph.add_edge("tech_support", "qa_inspector")
    graph.add_edge("chitchat", "qa_inspector")

    # Complaint 特殊处理：可能升级人工
    graph.add_conditional_edges("complaint", check_escalation, {
        "qa_inspector": "qa_inspector",
        "escalate": END,  # 升级人工时直接结束
    })

    # QA Inspector 后结束
    graph.add_edge("qa_inspector", END)

    return graph.compile()


# ======================== Gradio 前端 ========================

customer_service_app = build_customer_service_graph()


def handle_customer_message(message: str, history: list):
    """处理用户消息"""
    if not message.strip():
        return history, ""

    # 调用 Graph
    result = customer_service_app.invoke({
        "user_message": message,
    })

    # 提取回复和调试信息
    bot_response = result.get("response", "抱歉，系统出现问题，请稍后再试。")
    debug_info = "\n".join(result.get("debug_info", []))

    # 如果被升级人工，添加提示
    if result.get("escalated", False):
        bot_response += "\n\n*[已转接人工客服]*"

    # 添加调试信息（可选）
    if debug_info:
        bot_response += f"\n\n---\n<small>{debug_info}</small>"

    # 更新对话历史（使用新的字典格式）
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": bot_response})

    return history, ""


with gr.Blocks(theme=gr.themes.Soft(), title="智能客服系统") as chat_ui:
    gr.Markdown("# 🤖 智能客服系统\n多 Agent 协作：Router → [FAQ / 订单 / 技术支持 / 投诉 / 闲聊] → 质检")

    chatbot = gr.Chatbot(
        label="对话窗口",
        height=500,
    )

    with gr.Row():
        user_input = gr.Textbox(
            label="输入消息",
            placeholder="请输入您的问题...",
            scale=4
        )
        send_btn = gr.Button("发送", variant="primary", scale=1)

    # 快捷示例
    gr.Examples(
        examples=[
            "你好，我想了解退货政策",
            "帮我查询订单 12345 的物流",
            "我的 APP 总是闪退怎么办？",
            "你们的服务态度太差了，我要投诉！",
            "今天天气真不错",
        ],
        inputs=user_input,
    )

    # 绑定事件
    send_btn.click(
        fn=handle_customer_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input],
    )
    user_input.submit(
        fn=handle_customer_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input],
    )


if __name__ == "__main__":
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7891, share=False)
