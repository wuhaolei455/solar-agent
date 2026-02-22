# Demo 08: 深度研报系统 (Deep Research Report)

多 Agent 协作生成深度研究报告，展示 **Pipeline + Reflection** 架构模式。

## 架构图

```
START → Planner → Researcher → Analyst → Writer → Reviewer → END
                                           ↑          │
                                           └── revise ─┘ (max 2 rounds)
```

## Agent 角色

| Agent | 职责 | 技术要点 |
|-------|------|---------|
| Planner | 将主题拆解为 3-5 个子问题 | 结构化 JSON 输出 |
| Researcher | 对每个子问题搜集资料 | `create_react_agent` + 3 个搜索工具 |
| Analyst | 交叉分析，提炼关键洞察 | 多维度分析提示词 |
| Writer | 撰写结构化研报 | 支持根据 Review 反馈修改 |
| Reviewer | 质量审核（Reflection） | JSON 评分 + 条件路由 |

## 核心概念

### 1. StateGraph
使用 `langgraph.graph.StateGraph` 定义有向无环图（DAG），每个节点对应一个 Agent。

### 2. Reflection 模式
Reviewer → Writer 的条件循环：评分 < 7 且修改次数 < 3 时退回修改，否则输出最终研报。

### 3. ReAct Agent
Researcher 使用 `create_react_agent`，具备自主决策调用工具的能力（Reasoning + Acting）。

### 4. Annotated State
`research_data` 和 `progress` 使用 `Annotated[list, operator.add]`，支持多节点追加写入。

## 运行

```bash
make install DEMO=08
make run DEMO=08
```

浏览器打开 http://127.0.0.1:7890 即可使用。
