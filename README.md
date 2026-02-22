# solar-agent
这里是60天转大模型agent开发的学习仓库，欢迎志同道合的朋友们star关注来一起学习，希望我们可以一起协同进步，达成所愿！

扫码加微信，拉你进学习交流群 👇

<img src="./images/wechat.png" width="200" alt="微信二维码" />

## langchain学习

基于 LangChain + LangGraph 框架，从单个 LLM 调用到多 Agent 协作系统的完整学习路径。

### 基础系列（01-07）

| Demo | 名称 | 核心概念 | 关键 API |
|------|------|---------|---------|
| 01 | Weather Agent | Tool Use / ReAct | `create_react_agent` `@tool` |
| 02 | LCEL Chain | 链式编排 | `prompt \| model \| parser` |
| 03 | Gradio | Web UI 集成 | `gr.ChatInterface` |
| 04 | History Demo | 对话记忆管理 | `RunnableWithMessageHistory` |
| 05 | Stream | 流式输出 | `.stream()` + `yield` |
| 06 | Multimodal Voice | 多模态（ASR+TTS） | `whisper` `edge-tts` |
| 07 | Deep Thinking | 思维链推理 | Monkey Patch + `reasoning_content` |

### 高级多 Agent 系列（08-10）

| Demo | 名称 | 架构模式 | 核心概念 |
|------|------|---------|---------|
| 08 | 深度研报系统 | Pipeline + Reflection | `StateGraph` ReAct Agent 循环修正 |
| 09 | 智能客服系统 | Router + Handoff | 意图路由 Human-in-the-loop |
| 10 | AI 自媒体运营助手 | Planner + Parallel + Reflection | 并行节点 条件边 多平台适配 |

### 核心知识点速查

```
LangChain 三件套：
  Prompt Template  ──┐
  Chat Model       ──┼──▶  LCEL 管道（|）──▶  Output Parser
  Memory / History ──┘

LangGraph 图结构：
  StateGraph ──▶ 定义节点（Node = Agent/函数）
              ──▶ 添加边（顺序 / 条件）
              ──▶ compile() ──▶ .stream() / .invoke()

多 Agent 模式：
  Pipeline      顺序执行，适合固定流程
  Router        意图分发，适合多场景客服
  Reflection    循环修正，适合质量要求高的生成任务
  Parallel      并行加速，适合独立子任务
  Human-in-loop 人工介入，适合高风险决策
```

### 快速运行

```bash
# 安装依赖并运行某个 demo
make setup DEMO=08   # 深度研报
make setup DEMO=09   # 智能客服
make setup DEMO=10   # 自媒体助手
```

---

## deepmind学习

基于 [MiniMind](https://github.com/jingyaogong/minimind) 从零实现轻量级大语言模型，配合 [MiniMind-in-Depth](https://github.com/hans0809/MiniMind-in-Depth) 的深度源码解析系列，理解 LLM 底层原理。

### 🌱 基础构建

| # | 主题 | 你会学到 |
|---|------|---------|
| 1 | [如何从头训练 tokenizer](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/1-%E5%A6%82%E4%BD%95%E4%BB%8E%E5%A4%B4%E8%AE%AD%E7%BB%83tokenizer.md) | BPE 算法、词表构建、分词逻辑 |
| 2 | [RMSNorm 玄机](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/2-%E4%B8%80%E8%A1%8C%E4%BB%A3%E7%A0%81%E4%B9%8B%E5%B7%AE%EF%BC%8C%E6%A8%A1%E5%9E%8B%E6%80%A7%E8%83%BD%E6%8F%90%E5%8D%87%E8%83%8C%E5%90%8E%E7%9A%84RMSNorm%E7%8E%84%E6%9C%BA.md) | LayerNorm vs RMSNorm、训练稳定性 |
| 3 | [原始 Transformer 位置编码及缺陷](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/3-%E5%8E%9F%E5%A7%8BTransformer%E7%9A%84%E4%BD%8D%E7%BD%AE%E7%BC%96%E7%A0%81%E5%8F%8A%E5%85%B6%E7%BC%BA%E9%99%B7.md) | 正弦位置编码、长度外推问题 |
| 4 | [旋转位置编码 RoPE 全解析](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/4-%E6%97%8B%E8%BD%AC%E4%BD%8D%E7%BD%AE%E7%BC%96%E7%A0%81%E5%8E%9F%E7%90%86%E4%B8%8E%E5%BA%94%E7%94%A8%E5%85%A8%E8%A7%A3%E6%9E%90.md) | RoPE 原理、复数旋转、上下文扩展 |

### 🧱 架构进阶

| # | 主题 | 你会学到 |
|---|------|---------|
| 5 | [魔改注意力机制：效率优化大盘点](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/5-%E9%AD%94%E6%94%B9%E7%9A%84%E6%B3%A8%E6%84%8F%E5%8A%9B%E6%9C%BA%E5%88%B6%EF%BC%8C%E7%BB%86%E6%95%B0%E5%BD%93%E4%BB%A3LLM%E7%9A%84%E6%95%88%E7%8E%87%E4%BC%98%E5%8C%96%E6%89%8B%E6%AE%B5.md) | MHA → GQA → MQA、KV Cache、FlashAttention |
| 6 | [从稠密到稀疏：MoE 专家混合模型](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/6-%E4%BB%8E%E7%A8%A0%E5%AF%86%E5%88%B0%E7%A8%80%E7%96%8F%EF%BC%8C%E8%AF%A6%E8%A7%A3%E4%B8%93%E5%AE%B6%E6%B7%B7%E5%90%88%E6%A8%A1%E5%9E%8BMOE.md) | MoE 原理、Router 门控、负载均衡 |
| 7 | [像搭积木一样构建一个大模型](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/7-%E5%83%8F%E6%90%AD%E7%A7%AF%E6%9C%A8%E4%B8%80%E6%A0%B7%E6%9E%84%E5%BB%BA%E4%B8%80%E4%B8%AA%E5%A4%A7%E6%A8%A1%E5%9E%8B.md) | Embedding → Attention → FFN → LM Head 完整串联 |

### 🧪 训练与调优

| # | 主题 | 你会学到 |
|---|------|---------|
| 8 | [LLM 预训练流程全解](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/8-LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E6%B5%81%E7%A8%8B%E5%85%A8%E8%A7%A3.md) | 数据处理、损失函数、训练循环、checkpoint |
| 9 | [指令微调 SFT：从"能说"到"会听"](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/9-%E6%8C%87%E4%BB%A4%E5%BE%AE%E8%B0%83%E8%AF%A6%E8%A7%A3-%E8%AE%A9%E5%A4%A7%E6%A8%A1%E5%9E%8B%E4%BB%8E%E2%80%9C%E8%83%BD%E8%AF%B4%E2%80%9D%E5%8F%98%E5%BE%97%E2%80%9C%E4%BC%9A%E5%90%AC%E2%80%9D.md) | Chat 数据格式、指令跟随、掩码策略 |
| 10 | [DPO：大模型对齐训练新范式](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/10-DPO-%E5%A4%A7%E6%A8%A1%E5%9E%8B%E5%AF%B9%E9%BD%90%E8%AE%AD%E7%BB%83%E7%9A%84%E6%96%B0%E8%8C%83%E5%BC%8F.md) | RLHF vs DPO、偏好数据、隐式奖励 |

### 🧰 模型优化与压缩

| # | 主题 | 你会学到 |
|---|------|---------|
| 11 | [LoRA：LLM 轻量化微调的利器](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/11-LoRA-LLM%E8%BD%BB%E9%87%8F%E5%8C%96%E5%BE%AE%E8%B0%83%E7%9A%84%E5%88%A9%E5%99%A8.md) | 低秩分解原理、参数冻结、适配器插入 |
| 12 | [从白盒到黑盒：大模型蒸馏技术全掌握](https://github.com/hans0809/MiniMind-in-Depth/blob/main/src/12-%E4%BB%8E%E7%99%BD%E7%9B%92%E5%88%B0%E9%BB%91%E7%9B%92%EF%BC%8C%E5%85%A8%E9%9D%A2%E6%8E%8C%E6%8F%A1%E5%A4%A7%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF.md) | KD Loss、软标签、Teacher-Student 框架 |

> 源码解析项目地址：[MiniMind-in-Depth](https://github.com/hans0809/MiniMind-in-Depth) ｜ 原始项目：[MiniMind](https://github.com/jingyaogong/minimind)
