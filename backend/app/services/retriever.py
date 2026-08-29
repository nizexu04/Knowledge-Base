# backend/app/services/retriever.py
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from backend.app.config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

os.environ["HF_HUB_OFFLINE"] = "1"

class VectorRetriever:
    """
    基于 Chroma 的向量检索器（语义检索）
    """
    def __init__(self):
        print("🧠 正在加载嵌入模型 (BAAI/bge-m3)...")
        # 注意：这里的模型名称必须和建索引时完全一致
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        
        print(f"📂 正在连接向量数据库: {CHROMA_DB_PATH}")
        self.vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            persist_directory=CHROMA_DB_PATH,
            embedding_function=self.embeddings,
        )
        
        # 获取向量数量确认连接成功
        doc_count = self.vectorstore._collection.count()
        print(f"✅ 检索器初始化成功，共加载 {doc_count} 个向量")
        
    def retrieve(self, query: str, top_k: int = 5):
        """
        根据问题检索最相关的 top_k 个文本块
        返回格式: [(文本内容, 元数据, 距离分数), ...]
        
        注意：Chroma 默认使用余弦距离，分数越小表示越相关（0=完全相同，1=完全无关）
        """
        # similarity_search_with_score 返回 (Document, score)
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query, 
            k=top_k
        )
        
        results = []
        for doc, score in docs_with_scores:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,  # 分数越低越相关
                "file_name": doc.metadata.get("file_name", "未知文件")
            })
        
        return results

# 创建全局单例，便于后续 FastAPI 复用
_retriever_instance = None

def get_retriever():
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = VectorRetriever()
    return _retriever_instance

# ------ 独立运行测试入口 ------
if __name__ == "__main__":
    retriever = get_retriever()
    
    print("\n" + "=" * 60)
    print("🔍 向量检索测试模式 (输入 'exit' 退出)")
    print("=" * 60)
    
    while True:
        query = input("\n💬 请输入你的问题: ").strip()
        if query.lower() == 'exit':
            break
        if not query:
            continue
        
        # 检索 Top-3
        results = retriever.retrieve(query, top_k=3)
        
        print(f"\n📌 找到 {len(results)} 个相关片段:\n")
        for i, item in enumerate(results, 1):
            print(f"--- 片段 {i} (距离分数: {item['score']:.4f}) ---")
            print(f"📄 来源文件: {item['file_name']}")
            print(f"📝 内容预览:\n{item['content'][:200]}...\n")