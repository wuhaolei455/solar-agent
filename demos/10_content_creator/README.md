# Demo 10: AI 自媒体运营助手 (Content Creator Assistant)

多 Agent 协作完成自媒体内容创作全流程，展示 **Planner + Pipeline + Parallel + Reflection** 架构模式。

## 架构图

```
START → Planner → Trend Researcher → Content Creator
                                           ↓
                       ┌───────────────────┴───────────────────┐
                       ↓                                       ↓
                 Fact Checker                            SEO Optimizer
                 (并行执行)                               (并行执行)
                       ↓                                       ↓
                       └───────────────────┬───────────────────┘
                                           ↓
                                        Editor
                                      (审核评分)
                                           ↓
                              ┌────────────┴────────────┐
                              ↓                         ↓
                       score < 8                    score >= 8
                              ↓                         ↓
                    revise → Content Creator    Platform Adapter
                    (带反馈重写)                 (多平台适配)
                                                        ↓
                                                       END
```

## Agent 角色

| Agent | 职责 | 技术要点 |
|-------|------|---------|
| Planner | 任务规划和拆解 | 将内容创作拆解为 6 个步骤 |
| Trend Researcher | 热点调研 | Tool Use（搜索热点 + 竞品分析） |
| Content Creator | 内容创作 | 支持多种风格（专业/轻松/幽默）|
| Fact Checker | 事实核查 | 并行执行，检查数据准确性 |
| SEO Optimizer | SEO 优化 | 并行执行，优化标题和关键词 |
| Editor | 主编审核 | Reflection 模式，综合评分 |
| Platform Adapter | 平台适配 | 结构化输出（公众号/微博/小红书）|

## 核心概念

### 1. Planner 规划模式
Planner Agent 将用户主题拆解为明确的任务步骤（调研 → 创作 → 审核 → 优化 → 适配）。

### 2. Pipeline 流水线
任务按顺序流转：Planner → Researcher → Creator → [Checker + Optimizer] → Editor → Adapter。

### 3. 并行执行
Fact Checker 和 SEO Optimizer 并行执行，提高效率（都从 Content Creator 输出，都输入到 Editor）。

### 4. Reflection 循环
Editor 审核评分 < 8 时，将反馈传回 Content Creator 重写（最多 2 轮修改）。

### 5. 结构化输出
Platform Adapter 输出 JSON 格式的多平台内容（公众号、微博、小红书），每个平台有不同的标题、摘要、正文。

### 6. Tool Use
Trend Researcher 使用 2 个搜索工具：
- `search_hot_topics`: 搜索当前热点话题
- `search_competitor_content`: 分析爆款文章

## 支持的内容风格

| 风格 | 特点 | 适用场景 |
|------|------|---------|
| 专业 | 数据驱动、逻辑严密、术语准确 | 行业分析、技术解读 |
| 轻松 | 通俗易懂、多用比喻、案例丰富 | 科普教育、大众传播 |
| 幽默 | 轻松诙谐、适度调侃、接地气 | 年轻用户、娱乐化内容 |

## 多平台适配

| 平台 | 标题要求 | 正文长度 | 风格特点 |
|------|---------|---------|---------|
| 公众号 | 吸睛、包含数字或疑问 | 1500-2500字 | 完整论述、排版精美 |
| 微博 | 简短精炼（50字内） | 280字内 | 提炼核心 + 话题标签 |
| 小红书 | 口语化、接地气 | 800字内 | 多用 emoji、分段明确 |

## 运行

```bash
# 创建 requirements.txt
echo "gradio>=4.0.0
langchain>=0.1.0
langchain-openai>=0.0.5
langgraph>=0.0.30" > demos/10_content_creator/requirements.txt

# 安装依赖
make install DEMO=10

# 运行
make run DEMO=10
```

浏览器打开 http://127.0.0.1:7892 即可使用。

## 使用示例

**输入：**
- 主题：人工智能在教育行业的应用
- 风格：轻松

**输出：**
1. **进度日志**：显示各 Agent 的执行状态
2. **原稿**：完整的 1500-2500 字文章
3. **公众号版**：优化排版，适合公众号发布
4. **微博版**：280 字精炼版 + 话题标签
5. **小红书版**：800 字图文版 + emoji

## 扩展建议

1. **真实搜索集成**：接入微博热搜 API、百度指数、Google Trends
2. **图片生成**：调用 DALL-E / Midjourney 生成配图
3. **定时发布**：集成各平台 API，自动定时发布
4. **数据分析**：追踪发布后的阅读量、点赞数等数据
5. **爆款预测**：基于历史数据训练模型，预测内容爆款潜力
6. **多人协作**：支持多个创作者协同工作，角色分工
