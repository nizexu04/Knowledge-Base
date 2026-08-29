# backend/app/services/indexing.py
import os
import glob
from typing import List
from datetime import datetime

# LangChain 核心导入
from langchain_core.documents import Document

# 针对不同格式的专用加载器
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
    Docx2txtLoader,
)

# 导入配置
from backend.app.config import DATA_DIR, SUPPORTED_EXTENSIONS

def load_single_file(file_path: str) -> List[Document]:
    """
    根据文件扩展名，选择对应的加载器，加载单个文件。
    返回 Document 列表（PDF 可能有多页，返回多个 Document）
    """
    ext = os.path.splitext(file_path)[1].lower()
    docs = []
    
    try:
        if ext == ".txt":
            # 文本文件容易遇到编码问题，使用 autodetect_encoding
            loader = TextLoader(file_path, autodetect_encoding=True)
            docs = loader.load()
            
        elif ext == ".md":
            # Markdown 保留标题结构，此处先全文加载，后续分块时保留层级
            loader = UnstructuredMarkdownLoader(file_path, mode="single")
            docs = loader.load()
            
        elif ext == ".pdf":
            # PDF 默认按页拆分，此处先全部加载，后续再合并或分块
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            
        else:
            # 不支持的类型返回空
            return []
            
    except Exception as e:
        print(f"⚠️  文件加载失败 [{file_path}]: {e}")
        return []

    # ----- 关键步骤：提取元数据 (Metadata) -----
    file_stat = os.stat(file_path)
    base_name = os.path.basename(file_path)
    
    for doc in docs:
        # 清空 LangChain 自带的元数据，使用我们自己的标准元数据（防止冲突）
        doc.metadata.clear()
        
        # 注入标准元数据
        doc.metadata["source"] = file_path          # 绝对路径
        doc.metadata["file_name"] = base_name       # 文件名
        doc.metadata["file_type"] = ext             # 文件后缀
        doc.metadata["modified_time"] = datetime.fromtimestamp(
            file_stat.st_mtime
        ).isoformat()                               # 修改时间 ISO 格式
        doc.metadata["doc_id"] = f"{base_name}_{hash(file_path + str(doc.page_content[:50]))}" # 简易去重ID
        
    return docs

def load_all_documents() -> List[Document]:
    """
    遍历 DATA_DIR，加载所有支持格式的笔记，返回完整的 Document 列表。
    用于首次全量索引。
    """
    all_docs = []
    print(f"📂 开始扫描目录: {DATA_DIR}")
    
    # 遍历所有支持的后缀
    for ext in SUPPORTED_EXTENSIONS:
        # 递归查找 data 目录下的所有文件 (glob 支持 ** 递归)
        pattern = os.path.join(DATA_DIR, "**", f"*{ext}")
        files = glob.glob(pattern, recursive=True)
        
        for file_path in files:
            print(f"  正在载入: {file_path}")
            docs = load_single_file(file_path)
            if docs:
                all_docs.extend(docs)
                print(f"    ✅ 成功载入，共 {len(docs)} 个文档块")
            else:
                print(f"    ⚠️ 载入结果为空或失败")

    print(f"📊 扫描完成，共载入 {len(all_docs)} 个文档块 (来自 {len(files)} 个文件)")
    return all_docs

# 为了便于测试，加一个简单的独立运行入口
if __name__ == "__main__":
    # 如果你直接运行这个脚本，会执行一次载入测试
    docs = load_all_documents()
    if docs:
        print("\n------ 载入样例 (第一份文档) ------")
        sample = docs[0]
        print(f"内容预览: {sample.page_content[:200]}...")
        print(f"元数据: {sample.metadata}")
    else:
        print("❌ 未载入任何文档，请检查 data 目录下是否有笔记文件。")