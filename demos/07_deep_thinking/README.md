# Demo 07: 深度思考模式（Deep Thinking）

展示如何让 LLM 在回答前先进行推理思考，并将思考过程实时展示给用户。

## 功能特点

- **普通模式**：模型直接回答，响应快速
- **深度思考模式**：模型先思考再回答，用户可以展开查看完整推理过程

## 核心原理

### 1. Monkey Patch
Monkey Patch（猴子补丁）就是在运行时动态替换已有代码的行为，不修改原始源码。在这里修改了抽象模型接口的_convert_delta_to_message_chunk方法

LangChain 默认不支持模型返回的 `reasoning_content` 扩展字段。通过补丁拦截 `_convert_delta_to_message_chunk` 方法，将 `reasoning_content` 保留到 `chunk.additional_kwargs` 中。

```
模型返回 delta: { "reasoning_content": "让我想想...", "content": "" }
                        │
                        ▼
        Monkey Patch 保留到 additional_kwargs
                        │
                        ▼
chunk.additional_kwargs["reasoning_content"] = "让我想想..."
```

### 2. 流式输出分离
思考过程单独输出，不添加到历史对话中
```
流式 chunk 流：

chunk 1: reasoning_content = "用户说的是..."       → 思考（仅展示）
chunk 2: reasoning_content = "应该纠正为..."       → 思考（仅展示）
chunk 3: content = "Great try!"                    → 回答（存入记忆）
chunk 4: content = " Here's the correction..."     → 回答（存入记忆）
```

### 3. 不加 StrOutputParser

普通流式 demo 使用 `chain = prompt | model | StrOutputParser()`，会将输出转为纯字符串。  
本 demo 去掉了 `StrOutputParser`，保留原始 `AIMessageChunk` 对象，以便读取 `additional_kwargs.reasoning_content`。

## 运行

```bash
make install DEMO=07
make run DEMO=07
```

浏览器打开 http://127.0.0.1:7880 即可使用。

x## 模型配置

| 模式 | 模型 | 说明 |
|------|------|------|
| 普通模式 | `gpt-5.2`（.env 配置） | 直接回答，速度快 |
| 深度思考 | `deepseek-v3.2-think`（aihubmix） | 先推理再回答，可查看思考过程 |

## 注意事项

- 深度思考模式使用 `deepseek-v3.2-think`，通过 aihubmix 代理访问
- 该模型在流式返回时通过 `reasoning_content` 字段传递思考过程
- Monkey Patch 依赖 LangChain 内部实现，升级 `langchain-openai` 版本时需注意兼容性
