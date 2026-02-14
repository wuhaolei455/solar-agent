## python yield
1. 生成一个Generator函数
2. 惰性取数值，并不会第一次调用将所有值返回进内存，而是随yield取值



## python实现流式
在Gradio中是通过generator的机制实现流式，即yield方法，代码如下：

```python
def respond():
    yield "部分内容"
```


## sse
> 附：SSE介绍
> 在大多数 Web 应用中，LLM 的流式输出**最终都会落到一种机制上：SSE（Server-Sent Events）**。
>
> #### 1、为什么需要 SSE？
>
> **传统请求的问题**
>
> 在非流式模式下：
>
> ```text
> 浏览器 ── 请求 ──> 服务端
> 浏览器 <─ 完整响应 ─ 服务端（等 10 秒）
> ```
>
> 问题是：
>
> * 用户 **长时间看不到任何反馈**
> * 无法中途取消
> * 无法展示“思考过程”
>
> **流式请求的目标**
>
> 我们希望的是：
>
> ```text
> 浏览器 ── 请求 ──> 服务端
> 浏览器 <─ token 1
> 浏览器 <─ token 2
> 浏览器 <─ token 3
> ...
> ```
>
> 这正是 **SSE 解决的问题**。
>
>
> #### 2、什么是 SSE（Server-Sent Events）？
>
> **SSE 是一种服务端 → 浏览器 单向推送数据的 HTTP 流式机制**
>
> 特点：
>
> * 基于 **HTTP（不是 WebSocket）**
> * 长连接
> * 服务端可以不断 `push` 消息
> * 浏览器原生支持（`EventSource`）
>
>
> #### 3、SSE 的数据长什么样？
>
> SSE 的数据是**纯文本协议**，每条消息长这样：
>
> ```text
> data: Hello
> ```
>
> 多条连续发送：
>
> ```text
> data: Hello
> data: world
> data: !
> ```
>
> 浏览器会**一条一条接收并触发事件**。
>
>
> ### 四、LLM Streaming 与 SSE 的关系
>
> 在 LLM 场景中：
>
> ```text
> 模型生成 token
>     ↓
> 后端不断 flush 响应
>     ↓
> 通过 SSE 推送到前端
>     ↓
> 前端实时更新 UI
> ```
