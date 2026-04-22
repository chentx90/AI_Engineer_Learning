import os
import logging
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeBuilder")

def main():
    # 1. 加载文档
    logger.info("正在加载文档...")
    loader = TextLoader("knowledge_base/amazon_policy.txt", encoding="utf-8")
    docs = loader.load()

    # 2. 文本切割
    # chunk_size: 每块多大；chunk_overlap: 块与块之间重叠多少（防止一句话被从中间劈开）
    logger.info("正在切割文本...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=150,chunk_overlap=30)
    splits = text_splitter.split_documents(docs)
    logger.info(f"文档被切割成了{len(splits)}个小块")

    # 3. 向量化模型（Embedding）
    # 使用开源免费的 MiniLM 模型，第一次运行会自动下载模型权重（约 80MB）
    logger.info("正在加载词向量模型...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4. 存入向量数据库（vector store）
    logger.info("正在生成向量并存入数据库...")
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

    # 数据库保存本地
    vectorstore.save_local("knowledge_base/faiss_index")
    logger.info("✅ 知识库构建完成！已保存至 knowledge_base/faiss_index 目录。")

if __name__ == "__main__":
    main()
