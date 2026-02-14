# solar-agent

### 反思问题
- LangChain 在这里解决了什么？
- “模式切换”本质是什么？
- 流式输出到底发生在什么层？
- 一次对话，真正“不可控”的部分是哪一步？

### answer
- langchain集成了模型和工具函数, 提供了开箱即用的agent
(LangChain 提供了模型抽象、Prompt 模板、链式编排、记忆管理等统一接口，让切换模型只需改一行字符串，组装复杂流程只需用 | 管道符。)
- 本质是一个if/else
- 流式发生在
1. 模型层：逐 token 生成
     ↓
2. API 层：SSE (Server-Sent Events) 推送 chunk
      ↓
3. LangChain 层：.stream() 将 SSE 转为 Python 迭代器
      ↓
4. 应用层：yield 把每次累积的文本传递给框架
      ↓
5. Gradio 层：检测到 yield 就刷新聊天界面
- 不可控的是模型推理的部分，模型调用工具是可控的(输出格式也可控)

