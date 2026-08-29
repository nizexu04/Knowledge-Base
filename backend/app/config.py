# backend/app/config.py
import os

# 项目根目录 (假设当前文件在 backend/app/ 下，向上两级即为根目录)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 原始笔记存放目录
DATA_DIR = os.path.join(BASE_DIR, "data")

# 向量库持久化目录
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
CHROMA_DB_PATH = os.path.join(STORAGE_DIR, "chroma_db")
BM25_INDEX_PATH = os.path.join(STORAGE_DIR, "bm25_index.pkl")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

# 支持的文档格式
SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"]

#向量库集合名称
CHROMA_COLLECTION_NAME = "personal_notes"