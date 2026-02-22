# 高级多 Agent 系统设计指南

本文档详细对比三个高级 Demo（08-10），帮助理解不同的多 Agent 架构模式。

## 📊 三大系统对比

| 维度 | Demo 08<br/>深度研报系统 | Demo 09<br/>智能客服系统 | Demo 10<br/>自媒体运营助手 |
|------|------------------------|------------------------|--------------------------|
| **业务场景** | 研究报告生成 | 客户服务支持 | 内容创作与分发 |
| **核心架构** | Pipeline + Reflection | Router + Handoff | Planner + Parallel + Reflection |
| **Agent 数量** | 6 个 | 7 个 | 7 个 |
| **执行模式** | 串行 + 循环 | 条件路由 | 串行 + 并行 + 循环 |
| **交互方式** | 单次任务 | 多轮对话 | 单次任务 |
| **人工介入** | 无（全自动） | 有（投诉升级） | 无（全自动） |
| **复杂度** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **学习重点** | Reflection 循环 | 意图路由 + Handoff | 并行执行 + 结构化输出 |

---

## 🔬 Demo 08: 深度研报系统

### 架构特点
- **线性流水线**：任务按固定顺序执行（规划 → 调研 → 分析 → 撰写 → 审核）
- **质量循环**：Reviewer 评分 < 7 时，将反馈传回 Writer 修改（最多 3 轮）
- **ReAct Agent**：Researcher 自主决策调用搜索工具

### State 设计
```python
class ResearchState(TypedDict):
    topic: str                    # 用户输入
    sub_questions: list[str]      # 拆解的子问题
    research_data: Annotated[list[str], operator.add]  # 追加式写入
    analysis: str
    draft: str
    review: str
    review_score: int
    final_report: str
    revision_count: int
    progress: Annotated[list[str], operator.add]  # 进度日志
```

**核心技巧：** `Annotated[list, operator.add]` 允许多个节点向同一个 list 字段追加数据。

### 条件路由
```python
def should_revise(state: ResearchState) -> Literal["writer", "publish"]:
    score = state.get("review_score", 10)
    revision_count = state.get("revision_count", 0)

    if score < 7 and revision_count < 3:
        return "writer"  # 退回修改
    return "publish"      # 通过发布
```

### 适用场景
- 固定流程、步骤明确的任务
- 需要质量把关和迭代优化
- 长文本生成（研报、白皮书、分析报告）

---

## 🤖 Demo 09: 智能客服系统

### 架构特点
- **意图路由**：Router Agent 识别用户意图，分发到 5 个专业 Agent
- **责任明确**：每个 Agent 只处理特定类型的问题
- **升级机制**：Complaint Agent 判断是否需要转人工
- **质检节点**：所有回复都经过 QA Inspector 过滤

### State 设计
```python
class CustomerServiceState(TypedDict):
    user_message: str              # 用户输入
    intent: str                    # 识别出的意图
    response: str                  # Agent 回复
    qa_result: str                 # 质检结果
    qa_passed: bool                # 是否通过质检
    escalated: bool                # 是否升级人工
    debug_info: list[str]          # 调试信息
```

**核心技巧：** 使用 LLM 进行意图分类，返回标准类别名（faq / order / tech_support / complaint / chitchat）。

### 意图路由实现
```python
def route_by_intent(state: CustomerServiceState) -> Literal["faq", "order", "tech_support", "complaint", "chitchat"]:
    return state["intent"]  # 直接返回意图字段

# 在 Graph 中使用
graph.add_conditional_edges("router", route_by_intent, {
    "faq": "faq",
    "order": "order",
    "tech_support": "tech_support",
    "complaint": "complaint",
    "chitchat": "chitchat",
})
```

### Agent 分工

| Agent | 输入 | 工具 | 输出 | 特殊处理 |
|-------|------|------|------|---------|
| Router | 用户消息 | LLM 分类 | 意图类别 | - |
| FAQ | 用户消息 | 知识库检索 | 答案 | - |
| Order | 用户消息 | `query_order` + `check_logistics` | 订单信息 | ReAct Agent |
| Tech Support | 用户消息 | `diagnose_issue` | 诊断建议 | ReAct Agent |
| Complaint | 用户消息 | LLM 分析 | 回复 + 升级判断 | Human-in-the-loop |
| Chitchat | 用户消息 | LLM 对话 | 闲聊回复 | 兜底 |
| QA Inspector | Agent 回复 | 敏感词检测 | 过滤后回复 | 后置质检 |

### 适用场景
- 多场景分流（不同类型用户需求）
- 专业分工明确（每个 Agent 专注一个领域）
- 需要人工介入的场景（升级、审核）

---

## 📝 Demo 10: AI 自媒体运营助手

### 架构特点
- **任务规划**：Planner 拆解内容创作流程
- **并行执行**：Fact Checker 和 SEO Optimizer 同时运行
- **质量循环**：Editor 审核 → 评分 < 8 退回修改
- **结构化输出**：Platform Adapter 生成多平台格式 JSON

### State 设计
```python
class ContentCreationState(TypedDict):
    topic: str                          # 用户输入主题
    style: str                          # 内容风格
    plan: list[str]                     # 任务步骤
    trend_research: str                 # 热点调研
    draft: str                          # 内容初稿
    fact_check_result: str              # 事实核查
    seo_suggestions: str                # SEO 建议
    editor_review: str                  # 主编意见
    editor_score: int                   # 综合评分
    revision_count: int                 # 修改次数
    final_content: dict                 # 多平台格式
    progress: Annotated[list[str], operator.add]
```

### 并行执行实现
```python
# Content Creator 完成后，分叉到两个并行节点
graph.add_edge("content_creator", "fact_checker")
graph.add_edge("content_creator", "seo_optimizer")

# 两个并行节点都完成后，汇聚到 Editor
graph.add_edge("fact_checker", "editor")
graph.add_edge("seo_optimizer", "editor")
```

**关键：** LangGraph 会自动等待所有并行节点完成后，再执行下一个节点。

### 结构化输出示例
```json
{
  "wechat": {
    "title": "公众号标题",
    "summary": "摘要（100字）",
    "content": "完整正文（1500-2500字）"
  },
  "weibo": {
    "title": "微博标题（50字内）",
    "content": "微博正文（280字内）+ 话题标签"
  },
  "xiaohongshu": {
    "title": "小红书标题（口语化）",
    "content": "小红书正文（800字内）+ emoji"
  }
}
```

### 适用场景
- 复杂任务需要动态规划
- 部分子任务可以并行执行
- 需要多种格式输出（适配不同渠道）

---

## 🎓 学习路径建议

### 初学者（掌握基础）
1. **先学 Demo 08**
   - 理解 StateGraph 基本概念
   - 掌握线性流水线构建
   - 学会使用 Reflection 循环

### 进阶者（掌握路由）
2. **再学 Demo 09**
   - 理解条件路由机制
   - 掌握多 Agent 分工协作
   - 学会 Human-in-the-loop 设计

### 高级者（掌握复杂编排）
3. **最后学 Demo 10**
   - 理解并行执行原理
   - 掌握结构化输出技巧
   - 学会动态任务规划

---

## 🛠️ 通用设计模式

### 1. State 设计原则
- **最小化**：只存储必要信息，避免冗余
- **类型明确**：使用 TypedDict 定义清晰的字段类型
- **追加式字段**：使用 `Annotated[list, operator.add]` 支持多节点写入
- **调试信息**：添加 `debug_info` 或 `progress` 字段便于追踪

### 2. 条件路由设计
```python
# 方案 1：LLM 分类（适合复杂意图识别）
def router_with_llm(state):
    intent = llm.invoke(["classify this:", state["message"]]).content
    return intent

# 方案 2：规则判断（适合简单条件）
def router_with_rules(state):
    if state["score"] < 7:
        return "revise"
    return "publish"

# 方案 3：工具调用（适合需要外部数据）
def router_with_tool(state):
    result = check_user_permission(state["user_id"])
    return "admin" if result["is_admin"] else "user"
```

### 3. 并行执行设计
```python
# 从节点 A 分叉到 B 和 C（并行）
graph.add_edge("A", "B")
graph.add_edge("A", "C")

# B 和 C 都完成后，汇聚到 D
graph.add_edge("B", "D")
graph.add_edge("C", "D")
```

**注意：** 并行节点不能修改同一个非 `Annotated` 字段，否则会覆盖。

### 4. Reflection 循环设计
```python
def should_continue(state):
    if state["quality_score"] >= 8:
        return "end"
    if state["iteration"] >= 3:
        return "end"  # 防止无限循环
    return "revise"

graph.add_conditional_edges("reviewer", should_continue, {
    "revise": "writer",
    "end": END,
})
```

---

## 🚀 最佳实践

### 1. 调试技巧
- 使用 `progress` 字段记录每个节点的执行状态
- 打印 State 快照观察数据流转
- 使用 `stream_mode="updates"` 逐步观察节点输出

### 2. 性能优化
- 并行执行独立任务（事实核查 + SEO 优化）
- 减少不必要的 LLM 调用（能用规则就用规则）
- 使用更快的模型处理简单任务（如意图分类用 haiku）

### 3. 错误处理
- 为每个 Agent 添加 try-except 包裹
- 提供兜底逻辑（如意图识别失败 → 默认 chitchat）
- 设置最大循环次数，防止死循环

### 4. 可扩展性
- Agent 节点函数保持单一职责
- 使用配置文件管理 Agent 行为（如风格、评分阈值）
- 工具函数独立封装，便于替换（如模拟搜索 → 真实 API）

---

## 📦 三个系统的实际应用

### Demo 08：深度研报系统
**实际应用场景：**
- 投资机构的行业研究自动化
- 咨询公司的客户报告生成
- 媒体机构的深度调查报道

**扩展方向：**
- 接入真实搜索 API（Tavily、SerpAPI）
- 集成向量数据库（Chroma、Pinecone）存储历史研报
- 添加数据可视化节点（生成图表）

### Demo 09：智能客服系统
**实际应用场景：**
- 电商平台的客服机器人
- SaaS 产品的技术支持
- 政务服务的智能问答

**扩展方向：**
- 对接真实业务系统 API（订单、工单、CRM）
- 集成语音识别和合成（语音客服）
- 添加情绪分析和用户画像

### Demo 10：自媒体运营助手
**实际应用场景：**
- 自媒体团队的内容生产
- 企业的品牌营销内容
- 知识付费平台的课程内容

**扩展方向：**
- 接入真实热点 API（微博热搜、百度指数）
- 集成图片生成（DALL-E、Midjourney）
- 对接各平台发布 API，自动定时发布
- 添加数据分析节点，追踪内容效果

---

## 🎯 总结

| 系统 | 学习价值 | 生产就绪度 | 推荐指数 |
|------|---------|-----------|---------|
| Demo 08 | ⭐⭐⭐⭐ 理解 Reflection 循环 | ⭐⭐⭐ 需接入真实搜索 | ⭐⭐⭐⭐ |
| Demo 09 | ⭐⭐⭐⭐⭐ 最接近生产场景 | ⭐⭐⭐⭐ 需对接业务系统 | ⭐⭐⭐⭐⭐ |
| Demo 10 | ⭐⭐⭐⭐⭐ 覆盖最全概念 | ⭐⭐⭐ 需真实 API + 图片生成 | ⭐⭐⭐⭐⭐ |

**建议学习顺序：** 08 → 09 → 10

从简单到复杂，从单一模式到组合模式，逐步掌握多 Agent 系统设计。
