# backend/app/services/build_index.py
import sys
import os

# 将项目根目录添加到 Python 路径，方便直接运行此脚本
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import CharacterTextSplitter
from langchain_text_splitters import TokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from backend.app.config import DATA_DIR, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME
from backend.app.services.indexing import load_all_documents

def build_vector_index():
    """
    全量构建向量索引：载入文档 -> 分块 -> 嵌入 -> 存入 Chroma
    """
    print("=" * 50)
    print("🚀 开始构建向量索引...")
    print("=" * 50)

    # ----- 1. 载入原始文档 -----
    print("\n📄 步骤 1/4: 载入原始文档...")
    raw_docs = load_all_documents()
    if not raw_docs:
        print("❌ 错误: data 目录下没有找到可载入的文档，请检查！")
        return
    print(f"✅ 成功载入 {len(raw_docs)} 个文档片段（按文件页/段拆分）")

    # ----- 2. 文本分块 (Chunking) -----
    print("\n✂️ 步骤 2/4: 智能分块 (针对中英文优化)...")
    
    # 针对中英文混合优化的分隔符列表（优先按段落、句号、问号、感叹号切）
    separators = [
        "\n\n",  # 双换行（段落）
        "\n",    # 单换行
        "。",    # 中文句号
        "！",    # 中文感叹号
        "？",    # 中文问号
        "；",    # 中文分号
        "，",    # 中文逗号
        ".",     # 英文句号
        "!",     # 英文感叹号
        "?",     # 英文问号
        ";",     # 英文分号
        ",",     # 英文逗号
        " ",     # 空格
        ""       # 兜底（按字符）
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,          # 每块最大字符数（对于中文，512字约等于 300-400 tokens）
        chunk_overlap=128,       # 重叠字符数（保持上下文连贯）
        separators=separators,
        length_function=len,     # 按字符数计算长度
        keep_separator=False,    # 切分时不保留分隔符
    )

    # 执行分块（传入 Document 列表，返回新的 Document 列表，内容被切碎）
    chunked_docs = text_splitter.split_documents(raw_docs)
    print(f"✅ 分块完成，共生成 {len(chunked_docs)} 个文本块")

    # 打印一个样例块，方便检查分块效果
    if chunked_docs:
        print("\n📌 分块样例预览 (前100字符):")
        print(f"   {chunked_docs[0].page_content[:100]}...")
        print(f"   来源文件: {chunked_docs[0].metadata.get('file_name', '未知')}")

    # ----- 3. 嵌入模型 (Embedding) -----
    print("\n🧠 步骤 3/4: 加载嵌入模型 (BAAI/bge-m3)...")
    print("   (首次运行会自动下载模型，约 2.2GB，请耐心等待)")

    # 使用 BGE-M3 模型（中英混合表现极佳，支持稠密+稀疏，但此处我们只用稠密向量）
    # 如果电脑配置较低，可以换成更小的模型：BAAI/bge-small-zh-v1.5 (仅中文, 约 400MB)
    model_name = "BAAI/bge-m3"
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},  # Mac 默认用 CPU，如果装了 GPU 版 torch 可改为 'cuda'
        encode_kwargs={'normalize_embeddings': True},  # 归一化向量，提升检索效果
    )
    print("✅ 嵌入模型加载完成")

    # ----- 4. 存入 Chroma 向量库 -----
    print("\n💾 步骤 4/4: 存入 Chroma 向量数据库...")
    print(f"   存储路径: {CHROMA_DB_PATH}")
    print(f"   集合名称: {CHROMA_COLLECTION_NAME}")

    # 如果已存在同名集合，Chroma 默认会追加（添加新文档）。
    # 我们这里使用全量重建模式：删除旧数据，重新插入（适合个人笔记全量索引）
    # 如果不想每次删除旧数据，可以去掉下面的清空逻辑，改用 add_documents
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings,
    )

    # 清空旧数据（如果有），实现全量覆盖
    # 注意：Chroma 的 delete_collection 需要先获取 collection，这里用简单方式处理
    try:
        # 如果集合存在且不为空，删除集合重建（规避重复数据）
        if vectorstore._collection.count() > 0:
            print("   ⚠️ 检测到旧索引数据，正在清除...")
            # 删除整个集合（需要拿到底层 client）
            vectorstore._client.delete_collection(CHROMA_COLLECTION_NAME)
            # 重新创建空集合
            vectorstore = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                persist_directory=CHROMA_DB_PATH,
                embedding_function=embeddings,
            )
    except Exception as e:
        # 如果删除失败（比如集合不存在），忽略错误继续
        print(f"   (清除旧数据时无异常: {e})")
        pass

    # 批量插入分块后的文档 (Chroma 内部会自动完成嵌入计算)
    # 注意：chunked_docs 中的 metadata 会原样保存到 Chroma 的 metadata 字段中
    vectorstore.add_documents(chunked_docs)
    
    # 持久化（Chroma 在 add 后会自动持久化，但显式调用确保安全）
    # vectorstore.persist()
    
    # 获取最终数量
    final_count = vectorstore._collection.count()
    print(f"\n🎉 索引构建完成！共存入 {final_count} 个文本块到 Chroma")
    print(f"📁 向量库目录: {CHROMA_DB_PATH}")
    print("=" * 50)

if __name__ == "__main__":
    build_vector_index()