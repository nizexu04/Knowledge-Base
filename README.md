# Personal RAG Knowledge Base Q&A System
# 基于 RAG 的个人笔记知识库问答系统

> 采用 FastAPI + Streamlit 组合，从零构建本地化、可溯源、支持混合检索的智能笔记问答助手。

## 项目目标
构建一个完全运行在本地（或轻量服务器）的个人知识库问答系统。用户上传笔记（Markdown/PDF/Word等）后，可以通过自然语言提问，系统会从笔记中检索最相关的片段，并生成带有**引用来源**的准确回答。

##  核心特性 (Roadmap)
-  **项目脚手架搭建** (FastAPI + Streamlit 基本连通)
-  **离线索引管道**：支持多格式文档加载、元数据提取、层级感知分块
-  **混合检索 (Hybrid Search)**：向量检索 (语义) + BM25 (关键词) 融合召回
-  **精排重排序 (Rerank)**：引入 BGE Reranker 模型，提升 Top-K 准确率
-  **智能问答与溯源**：答案生成 + 自动标注引用来源（文件名/段落）
-  **增量更新机制**：监听笔记变动，自动增量更新向量库（基于 MD5 Hash）

## 命令行
- python -m backend.app.services.build_index 分块和嵌入data目录下的所有笔记
- uvicorn backend.app.main:app --reload --port 8000 启动后端
- streamlit run frontend/app.py 启动前端
