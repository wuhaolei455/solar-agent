"""
Demo 08: 深度研报系统 (Deep Research Report)

多 Agent 协作架构：Supervisor + Pipeline + Reflection
- Planner：将用户主题拆解为子研究问题
- Researcher：对每个子问题搜集资料（ReAct Agent + 工具）
- Analyst：交叉分析，提炼关键洞察
- Writer：撰写结构化研报
- Reviewer：质量审核，不合格退回修改（Reflection）

图结构：
  START → planner → researcher → analyst → writer → reviewer
                                             ↑          │
                                             └── revise ─┘ (max 2 rounds)
                                                        │
                                                        └── END (final_report)
"""

import os
import json
import operator
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
creative_llm = init_chat_model("openai:gpt-5.2", temperature=0.7)


# ======================== State 定义 ========================

class ResearchState(TypedDict):
    topic: str                    # 用户输入的研究主题
    sub_questions: list[str]      # Planner 拆解的子问题
    research_data: Annotated[list[str], operator.add]  # Researcher 搜集的资料（可追加）
    analysis: str                 # Analyst 分析结论
    draft: str                    # Writer 撰写的初稿
    review: str                   # Reviewer 的审核意见
    review_score: int             # Reviewer 的评分 (1-10)
    final_report: str             # 最终输出的研报
    revision_count: int           # 已修改次数
    progress: Annotated[list[str], operator.add]  # 各阶段进度日志


# ======================== 搜索工具（模拟）========================

@tool
def web_search(query: str) -> str:
    """搜索互联网获取相关信息。输入搜索关键词，返回搜索结果摘要。"""
    # 模拟搜索结果 — 实际项目中可接入 Tavily / SerpAPI 等
    return (
        f"【搜索结果 - {query}】\n"
        f"1. 根据最新研究数据显示，{query}领域在2024-2025年呈现显著增长趋势，"
        f"年均增长率约15-20%。\n"
        f"2. 行业专家指出，{query}的核心驱动因素包括技术创新、政策支持和市场需求三个维度。\n"
        f"3. 主要挑战包括：人才短缺、标准化不足、投资回报周期长等。\n"
        f"4. 预计到2026年，该领域市场规模将达到当前的2-3倍。\n"
        f"5. 领先企业已开始布局下一代技术路线，竞争格局正在重塑。"
    )


@tool
def search_academic_papers(query: str) -> str:
    """搜索学术论文和研究报告。输入研究主题，返回相关学术成果。"""
    return (
        f"【学术论文 - {query}】\n"
        f"1. 《{query}的前沿进展与未来展望》(2025) - 综述了该领域最新理论框架和实证研究。\n"
        f"2. 《基于数据驱动的{query}分析方法》(2024) - 提出了新的量化分析模型。\n"
        f"3. 《{query}的国际比较研究》(2025) - 对比了中美欧三大市场的发展路径。"
    )


@tool
def search_market_data(query: str) -> str:
    """搜索市场数据和统计信息。输入查询内容，返回相关市场数据。"""
    return (
        f"【市场数据 - {query}】\n"
        f"- 2024年市场规模：约 850 亿美元\n"
        f"- 2025年预估市场规模：约 1020 亿美元（同比增长 20%）\n"
        f"- 主要参与者市场份额：头部企业占比约 45%，中小企业占比 55%\n"
        f"- 投融资情况：2024年全年融资事件超 200 起，总额约 150 亿美元"
    )


# ======================== 各 Agent 节点 ========================

def planner_node(state: ResearchState) -> dict:
    """Planner Agent：拆解研究主题为子问题"""
    topic = state["topic"]

    response = llm.invoke([
        SystemMessage(content="""你是一位资深研究策划专家。
你的任务是将用户给出的研究主题拆解为 3-5 个具体的子研究问题。

要求：
1. 子问题应覆盖该主题的核心维度（现状、趋势、挑战、机遇等）
2. 子问题之间不重叠，且合在一起能全面覆盖主题
3. 每个子问题应具体、可搜索

请以 JSON 数组格式返回，例如：
["问题1", "问题2", "问题3"]

只返回 JSON，不要其他内容。"""),
        HumanMessage(content=f"研究主题：{topic}")
    ])

    try:
        # 尝试解析 JSON
        content = response.content.strip()
        # 处理可能的 markdown 代码块包裹
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        sub_questions = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        sub_questions = [
            f"{topic}的发展现状和市场规模",
            f"{topic}的核心技术和创新趋势",
            f"{topic}面临的主要挑战和风险",
            f"{topic}的未来发展前景和投资机会",
        ]

    return {
        "sub_questions": sub_questions,
        "progress": [f"📋 **Planner** 已将主题拆解为 {len(sub_questions)} 个子问题：\n" +
                     "\n".join(f"  {i+1}. {q}" for i, q in enumerate(sub_questions))]
    }


def researcher_node(state: ResearchState) -> dict:
    """Researcher Agent（ReAct）：对子问题搜集资料"""
    sub_questions = state["sub_questions"]

    # 为 Researcher 创建 ReAct Agent
    researcher = create_react_agent(
        model=llm,
        tools=[web_search, search_academic_papers, search_market_data],
        prompt=(
            "你是一位专业的研究员。针对给定的研究问题，使用搜索工具搜集全面的资料。"
            "请综合多个来源的信息，整理出结构化的研究素材。"
            "每个问题至少使用 2 个不同的搜索工具获取信息。"
        ),
    )

    all_data = []
    progress_log = []

    for i, question in enumerate(sub_questions):
        result = researcher.invoke({
            "messages": [HumanMessage(content=f"请针对以下问题进行深入研究：{question}")]
        })

        # 提取最终回答
        final_msg = result["messages"][-1].content
        all_data.append(f"### 子问题 {i+1}：{question}\n\n{final_msg}")
        progress_log.append(
            f"🔍 **Researcher** 完成子问题 {i+1}/{len(sub_questions)} 的资料搜集"
        )

    return {
        "research_data": all_data,
        "progress": progress_log
    }


def analyst_node(state: ResearchState) -> dict:
    """Analyst Agent：交叉分析，提炼关键洞察"""
    topic = state["topic"]
    research_data = "\n\n---\n\n".join(state["research_data"])

    response = llm.invoke([
        SystemMessage(content="""你是一位资深行业分析师。
根据提供的研究素材，进行交叉分析并提炼关键洞察。

请从以下维度进行分析：
1. **核心发现**：最重要的 3-5 个发现
2. **趋势判断**：未来 1-3 年的发展趋势
3. **风险评估**：主要风险因素和概率
4. **数据支撑**：关键数据点总结
5. **独特洞察**：基于交叉分析得出的独特见解

请输出结构化的分析报告。"""),
        HumanMessage(content=f"研究主题：{topic}\n\n研究素材：\n{research_data}")
    ])

    return {
        "analysis": response.content,
        "progress": ["📊 **Analyst** 已完成深度分析，提炼出关键洞察"]
    }


def writer_node(state: ResearchState) -> dict:
    """Writer Agent：撰写结构化研报"""
    topic = state["topic"]
    analysis = state["analysis"]
    review = state.get("review", "")

    revision_hint = ""
    if review:
        revision_hint = f"\n\n⚠️ 上一轮审核意见（请根据以下反馈修改）：\n{review}"

    response = creative_llm.invoke([
        SystemMessage(content=f"""你是一位专业的研报撰写人。
请根据分析师提供的分析结果，撰写一份完整的深度研究报告。

报告结构要求：
1. **摘要**（200字以内）
2. **研究背景与目的**
3. **核心发现**（分点论述，每点有数据支撑）
4. **趋势分析**
5. **风险与挑战**
6. **投资/行动建议**
7. **结论**

写作要求：
- 语言专业严谨，但不晦涩
- 每个论点都要有数据或事实支撑
- 使用 Markdown 格式
- 总字数 1500-2500 字{revision_hint}"""),
        HumanMessage(content=f"研究主题：{topic}\n\n分析结果：\n{analysis}")
    ])

    revision_count = state.get("revision_count", 0)
    label = "修改稿" if revision_count > 0 else "初稿"

    return {
        "draft": response.content,
        "revision_count": revision_count + 1,
        "progress": [f"✍️ **Writer** 已完成研报{label}（第 {revision_count + 1} 版）"]
    }


def reviewer_node(state: ResearchState) -> dict:
    """Reviewer Agent（Reflection）：审核研报质量"""
    draft = state["draft"]
    topic = state["topic"]

    response = llm.invoke([
        SystemMessage(content="""你是一位严格的研报审核专家。
请从以下维度对研报进行评分和审核：

1. **逻辑性** (1-10)：论证是否严密、结构是否清晰
2. **数据支撑** (1-10)：关键论点是否有数据佐证
3. **可读性** (1-10)：语言是否流畅、排版是否合理
4. **完整性** (1-10)：是否覆盖了主题的核心维度

请输出 JSON 格式：
{
  "scores": {"逻辑性": 8, "数据支撑": 7, "可读性": 9, "完整性": 8},
  "overall_score": 8,
  "passed": true,
  "feedback": "具体的审核意见和修改建议..."
}

overall_score >= 7 且无硬伤时 passed 为 true，否则为 false。
只返回 JSON，不要其他内容。"""),
        HumanMessage(content=f"研究主题：{topic}\n\n研报内容：\n{draft}")
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        score = result.get("overall_score", 7)
        feedback = result.get("feedback", "")
        passed = result.get("passed", score >= 7)
        scores_detail = result.get("scores", {})
    except (json.JSONDecodeError, KeyError):
        score = 7
        feedback = "审核通过，报告质量合格。"
        passed = True
        scores_detail = {}

    scores_str = " | ".join(f"{k}:{v}" for k, v in scores_detail.items()) if scores_detail else ""
    status = "✅ 通过" if passed else "🔄 需修改"

    return {
        "review": feedback,
        "review_score": score,
        "progress": [
            f"🔎 **Reviewer** 审核完成 — {status}（综合评分：{score}/10）\n"
            f"   {scores_str}\n"
            f"   意见：{feedback[:100]}..."
        ]
    }


def publish_node(state: ResearchState) -> dict:
    """输出最终研报"""
    return {
        "final_report": state["draft"],
        "progress": ["📄 **最终研报已生成** ✅"]
    }


# ======================== 条件路由 ========================

def should_revise(state: ResearchState) -> Literal["writer", "publish"]:
    """判断是否需要退回修改"""
    score = state.get("review_score", 10)
    revision_count = state.get("revision_count", 0)

    if score < 7 and revision_count < 3:
        return "writer"
    return "publish"


# ======================== 构建 Graph ========================

def build_research_graph():
    graph = StateGraph(ResearchState)

    # 添加节点
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("publish", publish_node)

    # 添加边
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "reviewer")

    # Reflection 条件边
    graph.add_conditional_edges("reviewer", should_revise, {
        "writer": "writer",
        "publish": "publish",
    })
    graph.add_edge("publish", END)

    return graph.compile()


# ======================== Gradio 前端 ========================

research_app = build_research_graph()


def run_research(topic: str):
    """流式运行研报系统，逐步返回进度"""
    if not topic.strip():
        yield "⚠️ 请输入研究主题", ""
        return

    progress_text = f"## 🚀 开始研究：{topic}\n\n"
    report_text = ""

    yield progress_text + "⏳ 正在启动研究流程...", report_text

    # 使用 stream 模式逐步获取各节点的输出
    for event in research_app.stream(
        {"topic": topic, "revision_count": 0},
        stream_mode="updates",
    ):
        for node_name, node_output in event.items():
            # 更新进度
            if "progress" in node_output:
                for log in node_output["progress"]:
                    progress_text += f"\n{log}\n"

            # 更新报告
            if "final_report" in node_output:
                report_text = node_output["final_report"]
            elif "draft" in node_output:
                report_text = f"*（草稿 - 审核中...）*\n\n{node_output['draft']}"

            yield progress_text, report_text

    # 最终输出
    if not report_text or report_text.startswith("*（草稿"):
        report_text = "⚠️ 研报生成未完成，请重试。"

    yield progress_text + "\n---\n🎉 **全部流程已完成！**", report_text


with gr.Blocks(theme=gr.themes.Soft(), title="深度研报系统") as chat_ui:
    gr.Markdown("# 📊 深度研报系统\n多 Agent 协作：Planner → Researcher → Analyst → Writer → Reviewer")

    with gr.Row():
        topic_input = gr.Textbox(
            label="研究主题",
            placeholder="例如：人工智能在医疗行业的应用前景",
            scale=4
        )
        run_btn = gr.Button("🚀 生成研报", variant="primary", scale=1)

    with gr.Row():
        with gr.Column(scale=1):
            progress_output = gr.Markdown(label="📋 研究进度", value="*等待输入主题...*")
        with gr.Column(scale=2):
            report_output = gr.Markdown(label="📄 研报内容", value="*研报将在这里显示...*")

    run_btn.click(
        fn=run_research,
        inputs=[topic_input],
        outputs=[progress_output, report_output],
    )

    gr.Examples(
        examples=[
            "人工智能在医疗行业的应用前景",
            "2025年全球新能源汽车市场分析",
            "大语言模型技术发展趋势与商业化路径",
        ],
        inputs=topic_input,
    )


if __name__ == "__main__":
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7890, share=False)
