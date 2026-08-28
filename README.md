# 📚 Personal RAG Knowledge Base Q&A System
# 基于 RAG 的个人笔记知识库问答系统

> 🚀 采用 FastAPI + Streamlit 组合，从零构建本地化、可溯源、支持混合检索的智能笔记问答助手。

## 🎯 项目目标
构建一个完全运行在本地（或轻量服务器）的个人知识库问答系统。用户上传笔记（Markdown/PDF/Word等）后，可以通过自然语言提问，系统会从笔记中检索最相关的片段，并生成带有**引用来源**的准确回答。

## 🧠 核心特性 (Roadmap)
- [x] **项目脚手架搭建** (FastAPI + Streamlit 基本连通)
- [ ] **离线索引管道**：支持多格式文档加载、元数据提取、层级感知分块
- [ ] **混合检索 (Hybrid Search)**：向量检索 (语义) + BM25 (关键词) 融合召回
- [ ] **精排重排序 (Rerank)**：引入 BGE Reranker 模型，提升 Top-K 准确率
- [ ] **智能问答与溯源**：答案生成 + 自动标注引用来源（文件名/段落）
- [ ] **增量更新机制**：监听笔记变动，自动增量更新向量库（基于 MD5 Hash）

## 🏗️ 技术栈选型
| 层级 | 技术选型 | 备注 |
| :--- | :--- | :--- |
| **后端服务** | Python 3.10 + FastAPI + Uvicorn | 提供 RESTful API，处理核心 RAG 逻辑 |
| **前端界面** | Streamlit | 纯 Python 快速搭建聊天界面，无需前端基础 |
| **嵌入模型** | BAAI/bge-m3 (本地部署) | 中英混合语义模型，支持稠密+稀疏检索 |
| **向量数据库** | Chroma (PersistentClient) | 轻量级本地向量存储，支持 Metadata 过滤 |
| **重排序模型** | BAAI/bge-reranker-v2-m3 | 对召回结果进行深度精排 |
| **分块策略** | LangChain + 自定义 Markdown 分割器 | 保留标题层级上下文 |

## 📂 项目目录结构
```text
.
├── backend/                     # 后端核心代码
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 应用入口 & 路由定义
│   │   ├── config.py            # 全局配置 (模型路径、分块大小等)
│   │   ├── models/              # Pydantic 数据模型 (请求/响应结构)
│   │   │   └── schemas.py
│   │   └── services/            # 核心业务逻辑层 (与 Streamlit 解耦)
│   │       ├── rag_engine.py    # RAG 核心类 (索引、检索、重排、生成)
│   │       ├── indexing.py      # 文档加载、分块、入库逻辑
│   │       └── retrieval.py     # 混合检索、RRF融合、Rerank逻辑
│   └── requirements.txt         # 后端依赖
│
├── frontend/                    # 前端界面代码
│   ├── app.py                   # Streamlit 主界面
│   └── requirements.txt         # 前端依赖 (通常与后端共用，可省略)
│
├── data/                        # 存放原始笔记文件 (Markdown/PDF等)
│   └── (你的笔记文件放在这里)
│
├── storage/                     # 本地数据持久化目录
│   ├── chroma_db/               # Chroma 向量库持久化路径
│   └── bm25_index.pkl           # BM25 倒排索引缓存
│
├── .env                         # 环境变量 (如 API_KEY，如有需要)
├── .gitignore                   # Git 忽略文件
└── README.md                    # 项目说明文档 (即本文件)