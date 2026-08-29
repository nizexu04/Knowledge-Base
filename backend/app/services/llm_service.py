# backend/app/services/llm_service.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Iterator

# 初始化 LM Studio 的客户端
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    model="master",
    # temperature=0.3,
    # max_tokens=2048,
    streaming=True,  # 开启流式模式（重要！）
)

# 非流式调用（保留，兼容旧代码）
def invoke_llm(messages):
    response = llm.invoke(messages)
    return response.content

# 流式调用（新增）
def stream_llm(messages) -> Iterator[str]:
    """
    流式调用 LLM，逐块返回生成的文本片段
    """
    for chunk in llm.stream(messages):
        # LangChain 的 chunk 包含 content，逐块 yield
        if chunk.content:
            yield chunk.content

# 测试
if __name__ == "__main__":
    messages = [
        SystemMessage(content="你是一个友好的助手。"),
        HumanMessage(content="请介绍一下你自己，分三点说。")
    ]
    print("流式输出测试：")
    for token in stream_llm(messages):
        print(token, end="", flush=True)