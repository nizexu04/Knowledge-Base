from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
# 导入你的服务模块和模型定义
from backend.app.services.qa_service import ask_question_with_sources, ask_question_stream
from backend.app.services.indexing import load_all_documents
from backend.app.services.retriever import get_retriever
from backend.app.models.schemas import (
    LoadStatusResponse,
    ChatRequest,
    ChatResponse,
    SourceDocument
)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Personal RAG Knowledge Base",
    description="基于 RAG 的个人笔记问答系统后端",
    version="1.0.0"
)

# 配置 CORS（允许前端跨域访问）
# 开发环境允许所有来源，生产环境应指定具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有域名（生产环境请改为具体前端地址）
    allow_credentials=True,
    allow_methods=["*"],          # 允许所有 HTTP 方法（GET, POST, OPTIONS 等）
    allow_headers=["*"],          # 允许所有请求头
)


# ----- 健康检查 / 根路径 -----
@app.get("/")
async def root():
    return {
        "message": "Personal RAG System is running!",
        "status": "healthy"
    }


# ----- 数据载入接口（全量索引重建） -----
@app.post("/api/v1/load", response_model=LoadStatusResponse)
async def load_data():
    """
    触发全量数据载入和索引构建。
    注意：此操作会删除原有索引并重新构建，适用于新增/修改笔记后重建。
    """
    try:
        # 调用 indexing.py 中的 load_all_documents（仅载入并返回文档列表）
        # 注意：这里只是载入文档并统计信息，并没有真正重建索引。
        # 如果你希望一键重建索引，建议在 load 接口中调用 build_index 的逻辑。
        # 但为了保持职责清晰，此处只做演示性载入统计。
        # 实际重建索引请运行 build_index.py 脚本。
        documents = load_all_documents()
        file_set = set()
        file_details = []
        for doc in documents:
            fname = doc.metadata.get("file_name", "unknown")
            if fname not in file_set:
                file_set.add(fname)
                file_details.append({
                    "file_name": fname,
                    "type": doc.metadata.get("file_type", ""),
                    "modified_time": doc.metadata.get("modified_time", "")
                })
        return LoadStatusResponse(
            status="success",
            total_files=len(file_set),
            total_documents=len(documents),
            file_details=file_details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据载入失败: {str(e)}")

    
@app.post("/api/v1/chat/stream")
def chat_stream(request: ChatRequest):
    """
    流式问答接口：逐块返回生成的答案
    前端会收到 Server-Sent Events (SSE) 格式的数据流
    """
    try:
        def generate():
            """生成 SSE 格式的流式数据"""
            # 获取流式生成器和引用来源
            result = ask_question_stream(request.question, top_k=request.top_k or 3)
            sources = result["sources"]
            stream_generator = result["stream"]
            
            # 发送引用来源（作为元数据）
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
            
            # 逐块发送答案内容
            for chunk in stream_generator:
                yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
            # 发送结束信号
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式生成失败: {str(e)}")


# ----- 问答接口（核心） -----
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    接收用户问题，检索知识库，生成带引用的回答。
    """
    try:
        # 调用 qa_service 中的函数，返回包含答案和来源的字典
        result = ask_question_with_sources(
            question=request.question,
            top_k=request.top_k if request.top_k else 3
        )
        
        # 构造响应对象
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceDocument(**src) for src in result["sources"]]
        )
    except Exception as e:
        # 捕获异常并返回 500 错误
        raise HTTPException(status_code=500, detail=f"生成回答失败: {str(e)}")


# ----- 可选：健康检查接口（便于监控） -----
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}


# ----- 统计接口：笔记数量和向量数 -----
@app.get("/api/v1/stats")
async def get_stats():
    try:
        retriever = get_retriever()
        vector_count = retriever.vectorstore._collection.count()
        return {
            "note_count": len(set(
                doc.metadata.get("file_name", "") 
                for doc in retriever.vectorstore.similarity_search("test", k=vector_count)
            )),
            "vector_count": vector_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ----- 直接运行此文件（调试用） -----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发时自动重启
    )