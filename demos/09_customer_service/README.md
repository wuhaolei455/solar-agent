# Demo 09: 智能客服系统 (Customer Service System)

多 Agent 协作处理客户服务场景，展示 **Router + Handoff + Human-in-the-loop** 架构模式。

## 架构图

```
                      ┌─ FAQ Agent
                      ├─ Order Agent (ReAct + Tools)
START → Router Agent ─┼─ Tech Support Agent (ReAct)
                      ├─ Complaint Agent (escalate?)
                      └─ Chitchat Agent
                          ↓
                      QA Inspector → END
                          ↓
                   (escalate → Human)
```

## Agent 角色

| Agent | 职责 | 技术要点 |
|-------|------|---------|
| Router | 意图识别，路由到专业 Agent | 条件路由 `add_conditional_edges` |
| FAQ | 基于知识库回答常见问题 | 关键词匹配 + LLM 兜底 |
| Order | 订单查询、物流查询 | `create_react_agent` + 2 个工具 |
| Tech Support | 技术故障诊断 | `create_react_agent` + 诊断工具 |
| Complaint | 投诉处理 + 升级判断 | 情感分析 + Human-in-the-loop |
| Chitchat | 闲聊兜底 | 通用对话 |
| QA Inspector | 质检回复、敏感词过滤 | 后置质检节点 |

## 核心概念

### 1. Router 模式
使用 LLM 识别用户意图（faq / order / tech_support / complaint / chitchat），通过 `add_conditional_edges` 路由到对应的专业 Agent。

### 2. Handoff（Agent 切换）
不同意图交给不同的专业 Agent 处理，各 Agent 之间互不干扰，清晰分工。

### 3. Human-in-the-loop
Complaint Agent 会判断投诉严重程度，决定是否升级人工客服（`escalated=True` 时跳转到 `END`）。

### 4. 质检节点
所有 Agent 的回复都要经过 QA Inspector 进行敏感词过滤和质量检查。

### 5. ReAct Agent
Order Agent 和 Tech Support Agent 使用 `create_react_agent`，可以自主决策调用工具。

## 支持的场景

| 用户输入 | 意图分类 | 处理 Agent | 工具调用 |
|---------|---------|-----------|---------|
| "我想了解退货政策" | faq | FAQ Agent | `search_faq` |
| "查询订单 12345" | order | Order Agent | `query_order` + `check_logistics` |
| "APP 闪退怎么办？" | tech_support | Tech Support Agent | `diagnose_issue` |
| "服务态度太差了！" | complaint | Complaint Agent | （可能升级人工） |
| "今天天气不错" | chitchat | Chitchat Agent | 无 |

## 运行

```bash
make install DEMO=09
make run DEMO=09
```

浏览器打开 http://127.0.0.1:7891 即可使用。

## 扩展建议

1. **真实 RAG 集成**：将 FAQ 知识库接入向量数据库（如 Chroma、Pinecone）
2. **真实 API 对接**：将订单查询、物流查询接入真实的业务系统 API
3. **多轮对话记忆**：为 Tech Support Agent 添加对话历史记忆，支持多轮诊断
4. **真实人工升级**：Complaint Agent 升级时，接入企业工单系统或人工坐席
5. **A/B 测试**：为不同的回复策略做效果对比
