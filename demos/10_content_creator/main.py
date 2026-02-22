"""
Demo 10: AI 自媒体运营助手 (Content Creator Assistant)

多 Agent 协作架构：Planner + Pipeline + Reflection + Human-in-the-loop
- Planner: 任务拆解（热点调研 → 内容创作 → 审核 → 优化）
- Trend Researcher: 热点话题调研（Tool Use: 搜索 API）
- Content Creator: 长文创作（支持多种风格）
- Fact Checker: 事实核查（并行）
- SEO Optimizer: SEO 优化（并行）
- Editor: 主编审核（Reflection）
- Platform Adapter: 多平台格式适配（结构化输出）

图结构：
  START → planner → trend_researcher → content_creator
                                           ↓
                      ┌─ fact_checker ──────┤
                      └─ seo_optimizer ─────┘
                                ↓
                            editor (review)
                                ↓
                   ┌─ revise → content_creator (带反馈)
                   └─ approve → platform_adapter → END
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

setup()

# ======================== 全局模型 ========================

llm = init_chat_model("openai:gpt-5.2", temperature=0)
creative_llm = init_chat_model("openai:gpt-5.2", temperature=0.8)


# ======================== State 定义 ========================

class ContentCreationState(TypedDict):
    topic: str                          # 用户输入的主题
    style: str                          # 内容风格（专业/轻松/幽默）
    plan: list[str]                     # Planner 拆解的任务步骤
    trend_research: str                 # 热点调研结果
    draft: str                          # 内容初稿
    fact_check_result: str              # 事实核查结果
    seo_suggestions: str                # SEO 优化建议
    editor_review: str                  # 主编审核意见
    editor_score: int                   # 主编评分 (1-10)
    revision_count: int                 # 修改次数
    final_content: dict                 # 最终内容（多平台格式）
    progress: Annotated[list[str], operator.add]  # 进度日志


# ======================== 搜索工具（模拟）========================

@tool
def search_hot_topics(keyword: str) -> str:
    """搜索当前热点话题和趋势。输入关键词，返回热点信息。"""
    # 模拟搜索结果 — 实际项目中可接入微博热搜、百度指数、Google Trends 等
    return (
        f"【热点调研 - {keyword}】\n\n"
        f"**热门话题：**\n"
        f"1. #{keyword}技术突破# - 热度指数 850,000\n"
        f"   最新消息：某知名企业宣布在{keyword}领域取得重大进展\n\n"
        f"2. #{keyword}应用案例# - 热度指数 620,000\n"
        f"   用户关注点：实际应用效果、成本、可行性\n\n"
        f"3. #{keyword}vs传统方案# - 热度指数 430,000\n"
        f"   讨论焦点：优势对比、适用场景、投资回报\n\n"
        f"**用户痛点：**\n"
        f"- 不清楚{keyword}的实际应用价值\n"
        f"- 担心技术不成熟、落地困难\n"
        f"- 希望看到真实案例和数据支撑\n\n"
        f"**内容建议角度：**\n"
        f"- 通俗讲解{keyword}的原理和价值\n"
        f"- 分享真实案例和数据\n"
        f"- 对比分析优劣势\n"
        f"- 预测未来发展趋势"
    )


@tool
def search_competitor_content(keyword: str) -> str:
    """搜索竞品内容和爆款文章。输入关键词，返回优秀内容参考。"""
    return (
        f"【竞品内容分析 - {keyword}】\n\n"
        f"**爆款文章标题：**\n"
        f"1. 《{keyword}：被低估的技术革命》- 10万+ 阅读\n"
        f"   成功要素：标题吸睛 + 数据可视化 + 案例丰富\n\n"
        f"2. 《一文读懂{keyword}的前世今生》- 8万+ 阅读\n"
        f"   成功要素：结构清晰 + 通俗易懂 + 配图精美\n\n"
        f"3. 《{keyword}实战指南：从0到1》- 6万+ 阅读\n"
        f"   成功要素：干货满满 + 可操作性强 + 用户痛点明确\n\n"
        f"**内容共性：**\n"
        f"- 标题包含数字、疑问或对比\n"
        f"- 开头直击用户痛点\n"
        f"- 正文有数据支撑和案例\n"
        f"- 结尾有行动指引"
    )


# ======================== Agent 节点 ========================

def planner_node(state: ContentCreationState) -> dict:
    """Planner Agent: 任务规划和拆解"""
    topic = state["topic"]
    style = state["style"]

    plan = [
        "📊 热点调研：搜索热门话题和用户痛点",
        f"✍️ 内容创作：撰写{style}风格的长文",
        "🔍 事实核查：验证数据和观点准确性",
        "🎯 SEO 优化：优化标题和关键词布局",
        "👔 主编审核：质量评估和改进建议",
        "📱 平台适配：生成多平台格式"
    ]

    return {
        "plan": plan,
        "progress": [f"📋 **Planner** 已制定内容创作计划（共 {len(plan)} 步）"]
    }


def trend_researcher_node(state: ContentCreationState) -> dict:
    """Trend Researcher Agent: 热点调研"""
    topic = state["topic"]

    # 调用搜索工具
    hot_topics = search_hot_topics.invoke({"keyword": topic})
    competitor_content = search_competitor_content.invoke({"keyword": topic})

    research_result = f"{hot_topics}\n\n---\n\n{competitor_content}"

    return {
        "trend_research": research_result,
        "progress": ["🔍 **Trend Researcher** 完成热点调研"]
    }


def content_creator_node(state: ContentCreationState) -> dict:
    """Content Creator Agent: 内容创作"""
    topic = state["topic"]
    style = state["style"]
    research = state["trend_research"]
    editor_review = state.get("editor_review", "")

    revision_hint = ""
    if editor_review:
        revision_hint = f"\n\n⚠️ 主编审核意见（请根据反馈修改）：\n{editor_review}"

    style_guide = {
        "专业": "使用专业术语，数据驱动，逻辑严密，适合行业从业者阅读",
        "轻松": "语言活泼，通俗易懂，多用比喻和案例，适合大众读者",
        "幽默": "轻松诙谐，适当调侃，段子和梗适度，适合年轻用户"
    }

    response = creative_llm.invoke([
        SystemMessage(content=f"""你是一位优秀的自媒体内容创作者。请根据调研结果撰写一篇高质量文章。

**风格要求：** {style_guide.get(style, "专业严谨")}

**文章结构：**
1. **吸睛标题**（包含数字、疑问或对比）
2. **开头**（直击痛点，引发共鸣）
3. **正文**（3-5 个小节，每节有小标题）
   - 通俗讲解核心概念
   - 真实案例和数据支撑
   - 优劣势对比分析
   - 未来趋势预测
4. **结尾**（总结 + 行动指引）

**写作要求：**
- 总字数 1500-2500 字
- 使用 Markdown 格式
- 每个观点都有数据或案例支撑
- 多用小标题、列表、加粗等排版元素{revision_hint}"""),
        HumanMessage(content=f"主题：{topic}\n\n调研结果：\n{research}")
    ])

    revision_count = state.get("revision_count", 0)
    label = "修改稿" if revision_count > 0 else "初稿"

    return {
        "draft": response.content,
        "revision_count": revision_count + 1,
        "progress": [f"✍️ **Content Creator** 完成{label}（第 {revision_count + 1} 版）"]
    }


def fact_checker_node(state: ContentCreationState) -> dict:
    """Fact Checker Agent: 事实核查（并行执行）"""
    draft = state["draft"]

    response = llm.invoke([
        SystemMessage(content="""你是专业的事实核查员。请检查文章中的数据、观点是否准确可信。

检查维度：
1. 数据来源是否可靠
2. 统计数字是否合理
3. 因果关系是否成立
4. 是否有常识性错误

请输出 JSON 格式：
{
  "issues": [
    {"location": "第X段", "problem": "问题描述", "severity": "高/中/低"}
  ],
  "overall": "整体评价",
  "passed": true/false
}

只返回 JSON，不要其他内容。"""),
        HumanMessage(content=draft)
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        issues = result.get("issues", [])
        passed = result.get("passed", True)

        if passed:
            fact_check_text = "✅ 事实核查通过，未发现明显问题"
        else:
            issues_text = "\n".join([f"- {issue['location']}: {issue['problem']}" for issue in issues[:3]])
            fact_check_text = f"⚠️ 发现 {len(issues)} 处问题：\n{issues_text}"
    except (json.JSONDecodeError, KeyError):
        fact_check_text = "✅ 事实核查通过"

    return {
        "fact_check_result": fact_check_text,
        "progress": ["🔍 **Fact Checker** 完成事实核查"]
    }


def seo_optimizer_node(state: ContentCreationState) -> dict:
    """SEO Optimizer Agent: SEO 优化建议（并行执行）"""
    draft = state["draft"]
    topic = state["topic"]

    response = llm.invoke([
        SystemMessage(content="""你是 SEO 优化专家。请分析文章的 SEO 表现并提供优化建议。

分析维度：
1. 标题是否包含关键词
2. 关键词密度是否合理
3. 小标题结构是否清晰
4. 是否有内外链机会
5. meta 描述建议

请给出具体的优化建议（3-5 条）。"""),
        HumanMessage(content=f"主题关键词：{topic}\n\n文章内容：\n{draft}")
    ])

    return {
        "seo_suggestions": response.content,
        "progress": ["🎯 **SEO Optimizer** 完成 SEO 分析"]
    }


def editor_node(state: ContentCreationState) -> dict:
    """Editor Agent: 主编审核（Reflection）"""
    draft = state["draft"]
    fact_check = state["fact_check_result"]
    seo = state["seo_suggestions"]

    response = llm.invoke([
        SystemMessage(content="""你是资深内容主编。请综合评估文章质量并给出审核意见。

评估维度：
1. **吸引力** (1-10)：标题和开头是否吸睛
2. **内容质量** (1-10)：论证是否充分、案例是否丰富
3. **可读性** (1-10)：排版是否清晰、语言是否流畅
4. **事实准确性** (1-10)：基于事实核查结果
5. **SEO 友好度** (1-10)：基于 SEO 分析结果

请输出 JSON 格式：
{
  "scores": {"吸引力": 8, "内容质量": 7, ...},
  "overall_score": 8,
  "passed": true,
  "feedback": "具体的审核意见和修改建议..."
}

overall_score >= 8 且无硬伤时 passed 为 true，否则为 false。
只返回 JSON，不要其他内容。"""),
        HumanMessage(content=f"文章：\n{draft}\n\n事实核查：{fact_check}\n\nSEO 分析：{seo}")
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(content)
        score = result.get("overall_score", 8)
        feedback = result.get("feedback", "")
        passed = result.get("passed", score >= 8)
        scores_detail = result.get("scores", {})
    except (json.JSONDecodeError, KeyError):
        score = 8
        feedback = "审核通过，内容质量合格。"
        passed = True
        scores_detail = {}

    scores_str = " | ".join(f"{k}:{v}" for k, v in scores_detail.items()) if scores_detail else ""
    status = "✅ 通过" if passed else "🔄 需修改"

    return {
        "editor_review": feedback,
        "editor_score": score,
        "progress": [
            f"👔 **Editor** 审核完成 — {status}（综合评分：{score}/10）\n"
            f"   {scores_str}\n"
            f"   意见：{feedback[:80]}..."
        ]
    }


def platform_adapter_node(state: ContentCreationState) -> dict:
    """Platform Adapter Agent: 多平台格式适配"""
    draft = state["draft"]

    response = llm.invoke([
        SystemMessage(content="""你是多平台内容适配专家。请将文章改编为不同平台格式。

请输出 JSON 格式（包含 3 个平台版本）：
{
  "wechat": {
    "title": "适合公众号的标题",
    "summary": "摘要（100字内）",
    "content": "完整内容（保留原文核心，优化排版）"
  },
  "weibo": {
    "title": "微博标题（50字内）",
    "content": "微博正文（280字内，提炼核心观点 + 话题标签）"
  },
  "xiaohongshu": {
    "title": "小红书标题（吸睛、口语化）",
    "content": "小红书正文（800字内，多用 emoji、分段明确）"
  }
}

只返回 JSON，不要其他内容。"""),
        HumanMessage(content=draft)
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        final_content = json.loads(content)
    except (json.JSONDecodeError, KeyError):
        final_content = {
            "wechat": {"title": "内容标题", "content": draft},
            "weibo": {"title": "内容标题", "content": draft[:280]},
            "xiaohongshu": {"title": "内容标题", "content": draft[:800]},
        }

    return {
        "final_content": final_content,
        "progress": ["📱 **Platform Adapter** 完成多平台格式适配"]
    }


# ======================== 条件路由 ========================

def should_revise(state: ContentCreationState) -> Literal["content_creator", "platform_adapter"]:
    """判断是否需要修改"""
    score = state.get("editor_score", 10)
    revision_count = state.get("revision_count", 0)

    if score < 8 and revision_count < 2:
        return "content_creator"
    return "platform_adapter"


# ======================== 构建 Graph ========================

def build_content_creation_graph():
    graph = StateGraph(ContentCreationState)

    # 添加节点
    graph.add_node("planner", planner_node)
    graph.add_node("trend_researcher", trend_researcher_node)
    graph.add_node("content_creator", content_creator_node)
    graph.add_node("fact_checker", fact_checker_node)
    graph.add_node("seo_optimizer", seo_optimizer_node)
    graph.add_node("editor", editor_node)
    graph.add_node("platform_adapter", platform_adapter_node)

    # 添加边
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "trend_researcher")
    graph.add_edge("trend_researcher", "content_creator")

    # 并行执行事实核查和 SEO 优化
    graph.add_edge("content_creator", "fact_checker")
    graph.add_edge("content_creator", "seo_optimizer")

    # 两个并行任务完成后，进入主编审核
    graph.add_edge("fact_checker", "editor")
    graph.add_edge("seo_optimizer", "editor")

    # 主编审核后，条件路由
    graph.add_conditional_edges("editor", should_revise, {
        "content_creator": "content_creator",
        "platform_adapter": "platform_adapter",
    })

    graph.add_edge("platform_adapter", END)

    return graph.compile()


# ======================== Gradio 前端 ========================

content_creation_app = build_content_creation_graph()


def create_content(topic: str, style: str):
    """流式运行内容创作系统"""
    if not topic.strip():
        yield "⚠️ 请输入内容主题", "", "", ""
        return

    progress_text = f"## 🚀 开始创作：{topic}（风格：{style}）\n\n"
    draft_text = ""
    wechat_text = ""
    other_platforms_text = ""

    yield progress_text + "⏳ 正在启动内容创作流程...", draft_text, wechat_text, other_platforms_text

    # 流式执行
    for event in content_creation_app.stream(
        {"topic": topic, "style": style, "revision_count": 0},
        stream_mode="updates",
    ):
        for node_name, node_output in event.items():
            # 更新进度
            if "progress" in node_output:
                for log in node_output["progress"]:
                    progress_text += f"\n{log}\n"

            # 更新草稿
            if "draft" in node_output:
                draft_text = node_output["draft"]

            # 更新最终内容
            if "final_content" in node_output:
                final = node_output["final_content"]
                wechat = final.get("wechat", {})
                weibo = final.get("weibo", {})
                xiaohongshu = final.get("xiaohongshu", {})

                wechat_text = f"# {wechat.get('title', '')}\n\n{wechat.get('content', '')}"

                other_platforms_text = f"## 📱 微博版本\n\n**标题：** {weibo.get('title', '')}\n\n{weibo.get('content', '')}\n\n"
                other_platforms_text += f"---\n\n## 📱 小红书版本\n\n**标题：** {xiaohongshu.get('title', '')}\n\n{xiaohongshu.get('content', '')}"

            yield progress_text, draft_text, wechat_text, other_platforms_text

    yield progress_text + "\n---\n🎉 **内容创作完成！**", draft_text, wechat_text, other_platforms_text


with gr.Blocks(theme=gr.themes.Soft(), title="AI 自媒体运营助手") as chat_ui:
    gr.Markdown("# 📝 AI 自媒体运营助手\n多 Agent 协作：Planner → Researcher → Creator → [Fact Check + SEO] → Editor → Platform Adapter")

    with gr.Row():
        topic_input = gr.Textbox(
            label="内容主题",
            placeholder="例如：人工智能在教育行业的应用",
            scale=3
        )
        style_input = gr.Dropdown(
            label="内容风格",
            choices=["专业", "轻松", "幽默"],
            value="轻松",
            scale=1
        )
        create_btn = gr.Button("🚀 开始创作", variant="primary", scale=1)

    with gr.Row():
        with gr.Column(scale=1):
            progress_output = gr.Markdown(label="📋 创作进度", value="*等待输入主题...*")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📄 原稿"):
                    draft_output = gr.Markdown(value="*内容初稿将在这里显示...*")
                with gr.Tab("📱 公众号版"):
                    wechat_output = gr.Markdown(value="*公众号版本将在这里显示...*")
                with gr.Tab("📱 其他平台"):
                    other_output = gr.Markdown(value="*微博和小红书版本将在这里显示...*")

    create_btn.click(
        fn=create_content,
        inputs=[topic_input, style_input],
        outputs=[progress_output, draft_output, wechat_output, other_output],
    )

    gr.Examples(
        examples=[
            ["人工智能在教育行业的应用", "轻松"],
            ["2025年新能源汽车市场趋势", "专业"],
            ["程序员如何高效学习新技术", "幽默"],
        ],
        inputs=[topic_input, style_input],
    )


if __name__ == "__main__":
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
    chat_ui.launch(server_name="127.0.0.1", server_port=7892, share=False)
