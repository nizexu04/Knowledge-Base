# backend/app/services/qa_service.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from typing import Iterator, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.retriever import get_retriever
from backend.app.services.llm_service import stream_llm, llm
from langchain_core.messages import SystemMessage, HumanMessage

# ----- 1. 建提示模板（对应文档中的"建提示模板"） -----
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的个人知识库助手。
请严格基于以下【参考内容】来回答用户的问题。
如果参考内容中没有相关信息，请直接回答"根据现有笔记无法回答该问题"。
在回答中，如果引用了某段参考内容，请在其后标注对应的编号，例如 [1]。

【参考内容】
{context}
"""),
    ("human", "{question}")
])

# 创建处理链（将模板和 LLM 串起来）
qa_chain = prompt_template | llm


# ----- 2. 核心问答函数（对应文档中的"将问题与文本块相结合"） -----
def ask_question(question: str, top_k: int = 3) -> str:
    """
    处理用户问题：检索 -> 构建 Prompt -> 调用 LLM 生成答案
    """
    # 步骤 A：检索相关知识块
    retriever = get_retriever()
    raw_results = retriever.retrieve(question, top_k=top_k)
    
    if not raw_results:
        return "未找到与您问题相关的笔记内容。"
    
    # 步骤 B：将检索结果格式化为带编号的上下文
    contexts = []
    for i, item in enumerate(raw_results, 1):
        file_name = item.get("file_name", "未知文件")
        content = item.get("content", "")
        contexts.append(f"[{i}] 来自文件《{file_name}》\n{content}")
    
    context_text = "\n\n---\n\n".join(contexts)
    
    # 步骤 C：调用 LLM（将问题与文本块以 Prompt 形式传递）
    response = qa_chain.invoke({
        "context": context_text,
        "question": question
    })
    
    return response.content


# ----- 3. 独立测试入口 -----
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 RAG 问答系统 (检索 + 生成)")
    print("=" * 60)
    print("提示: 输入 'exit' 退出\n")
    
    while True:
        question = input("💬 请输入你的问题: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue
        
        print("\n⏳ 正在检索并生成答案...\n")
        answer = ask_question(question, top_k=3)
        
        print("=" * 60)
        print("📝 回答:")
        print(answer)
        print("=" * 60)
        print()

def ask_question_with_sources(question: str, top_k: int = 3) -> dict:
    """
    返回包含答案和引用来源的字典，用于前端展示
    """
    retriever = get_retriever()
    raw_results = retriever.retrieve(question, top_k=top_k)
    
    if not raw_results:
        return {
            "answer": "未找到与您问题相关的笔记内容。",
            "sources": []
        }
    
    # 提取引用来源（文件名 + 内容预览，方便前端展示）
    sources = []
    for item in raw_results:
        sources.append({
            "file_name": item.get("file_name", "未知文件"),
            "content": item.get("content", "")  # 可以直接展示原文
        })
    
    # 构建上下文（逻辑不变）
    contexts = []
    for i, item in enumerate(raw_results, 1):
        file_name = item.get("file_name", "未知文件")
        content = item.get("content", "")
        contexts.append(f"[{i}] 来自文件《{file_name}》\n{content}")
    context_text = "\n\n---\n\n".join(contexts)
    
    # 生成答案
    response = qa_chain.invoke({
        "context": context_text,
        "question": question
    })
    
    return {
        "answer": response.content,
        "sources": sources
    }



def ask_question_stream(question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    流式问答，返回一个生成器和引用来源
    """
    # 1. 检索
    retriever = get_retriever()
    raw_results = retriever.retrieve(question, top_k=top_k)
    
    if not raw_results:
        return {
            "sources": [],
            "stream": iter(["未找到与您问题相关的笔记内容。"])  # 直接返回错误消息
        }
    
    # 2. 构建上下文
    contexts = []
    sources = []
    for i, item in enumerate(raw_results, 1):
        file_name = item.get("file_name", "未知文件")
        content = item.get("content", "")
        score = float(item.get("score", 0))
        contexts.append(f"[{i}] 来自文件《{file_name}》\n{content}")
        sources.append({
            "file_name": file_name,
            "content": content,
            "score": score
        })
    
    context_text = "\n\n---\n\n".join(contexts)
    
    # 3. 构建 System Prompt
    system_prompt = f"""你是一个专业的个人知识库助手。
请严格基于以下【参考内容】来回答用户的问题。
如果参考内容中没有相关信息，请直接回答"根据现有笔记无法回答该问题"。
在回答中，如果引用了某段参考内容，请在其后标注对应的编号，例如 [1]。

【参考内容】
{context_text}
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ]
    
    # 4. 返回流式生成器和引用来源
    return {
        "sources": sources,
        "stream": stream_llm(messages)  # 这是生成器
    }