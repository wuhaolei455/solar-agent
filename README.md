# solar-agent

LangChain + LangGraph 多 Agent 系统学习项目，从基础到高级的完整示例。

## 📚 Demo 列表

### 基础系列（01-07）

| Demo | 名称 | 核心概念 | 端口 |
|------|------|---------|------|
| 01 | Weather Agent | Tool Use 基础 | - |
| 02 | LCEL Chain | 链式编排 | - |
| 03 | Gradio | Web UI 集成 | - |
| 04 | History Demo | 对话记忆管理 | - |
| 05 | Stream | 流式输出 | - |
| 06 | Multimodal Voice | 多模态交互 | - |
| 07 | Deep Thinking | 思维链推理 | - |

### 高级多 Agent 系列（08-10）

| Demo | 名称 | 架构模式 | 核心概念 | 端口 |
|------|------|---------|---------|------|
| **08** | 深度研报系统 | **Pipeline + Reflection** | Supervisor、ReAct Agent、循环修正 | 7890 |
| **09** | 智能客服系统 | **Router + Handoff** | 意图路由、专业 Agent、Human-in-the-loop | 7891 |
| **10** | AI 自媒体运营助手 | **Planner + Parallel + Reflection** | 任务规划、并行执行、多平台适配 | 7892 |

## 🎯 核心概念对照表

### LangChain 核心能力

| 能力 | 说明 | 示例 Demo |
|------|------|----------|
| 模型抽象 | `init_chat_model("openai:xxx")` 一行切换模型 | 所有 demo |
| Prompt 模板 | `ChatPromptTemplate` 结构化管理提示词 | 02-07 |
| 链式组合 | `prompt \| model \| parser` LCEL 管道 | 02-07 |
| 记忆管理 | `RunnableWithMessageHistory` 自动注入历史 | 04-07 |
| 工具调用 | Agent + Tool 编排 | 01, 08-10 |

### LangGraph 多 Agent 架构

| 架构模式 | 说明 | 使用场景 | Demo |
|---------|------|---------|------|
| **Pipeline** | 线性流水线，任务顺序执行 | 固定流程、步骤明确 | 08 |
| **Supervisor** | 中心调度，多 Agent 并行 | 任务可并行、需协调 | 08 |
| **Router** | 意图路由，按类型分发 | 多场景分流 | 09 |
| **Handoff** | Agent 间交接和切换 | 专业分工、责任明确 | 09 |
| **Planner** | 动态任务拆解和规划 | 复杂流程、需灵活调度 | 10 |
| **Reflection** | 质量审核 + 循环修正 | 需迭代优化的任务 | 08, 10 |
| **Parallel** | 并行执行多个 Agent | 独立任务、提升效率 | 10 |
| **Human-in-the-loop** | 关键节点人工介入 | 需人工决策的场景 | 09 |

## 🚀 快速开始

```bash
# 克隆项目
git clone <repo-url>
cd solar-agent

# 运行某个 demo（以 08 为例）
make install DEMO=08
make run DEMO=08
```

## 💡 架构设计思路

### Demo 08：深度研报系统
```
START → Planner → Researcher → Analyst → Writer → Reviewer → END
                                           ↑          │
                                           └── revise ─┘ (max 2 rounds)
```
**关键特性：**
- Planner 拆解研究问题
- Researcher 使用 ReAct Agent 自主调用搜索工具
- Reflection 循环：评分 < 7 退回修改
- Annotated State 支持多节点追加写入

### Demo 09：智能客服系统
```
                      ┌─ FAQ Agent
                      ├─ Order Agent (ReAct)
START → Router Agent ─┼─ Tech Support Agent (ReAct)
                      ├─ Complaint Agent (escalate?)
                      └─ Chitchat Agent
                          ↓
                      QA Inspector → END
```
**关键特性：**
- Router 意图识别（LLM 分类）
- 条件路由到 5 个专业 Agent
- Complaint Agent 支持升级人工
- QA Inspector 敏感词过滤

### Demo 10：AI 自媒体运营助手
```
START → Planner → Trend Researcher → Content Creator
                                           ↓
                       ┌───────────────────┴───────────────────┐
                 Fact Checker                            SEO Optimizer
                 (并行执行)                               (并行执行)
                       └───────────────────┬───────────────────┘
                                           ↓
                                        Editor
                                           ↓
                              ┌────────────┴────────────┐
                       score < 8                    score >= 8
                              ↓                         ↓
                    revise → Content Creator    Platform Adapter → END
```
**关键特性：**
- Planner 任务规划
- 并行执行（Fact Checker + SEO Optimizer）
- Reflection 循环（Editor 审核 + 修改）
- 结构化输出（多平台格式 JSON）

## 🤔 反思问题

### LangChain 在这里解决了什么？
LangChain 提供了模型抽象、Prompt 模板、链式编排、记忆管理等统一接口，让切换模型只需改一行字符串，组装复杂流程只需用 | 管道符。

### "模式切换"本质是什么？
本质是条件路由（if/else），通过 `add_conditional_edges` 根据 State 动态决定下一步走向。

### 流式输出到底发生在什么层？
```
1. 模型层：逐 token 生成
     ↓
2. API 层：SSE (Server-Sent Events) 推送 chunk
     ↓
3. LangChain 层：.stream() 将 SSE 转为 Python 迭代器
     ↓
4. 应用层：yield 把每次累积的文本传递给框架
     ↓
5. Gradio 层：检测到 yield 就刷新聊天界面
```

### 一次对话，真正"不可控"的部分是哪一步？
**不可控：** 模型推理生成文本的过程（概率采样）
**可控：** 模型调用工具、输出格式（通过 JSON Schema 约束）

