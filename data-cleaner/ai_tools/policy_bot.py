import os
import logging
from dotenv import load_dotenv
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from sympy.physics.mechanics import system

load_dotenv()
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def main():
    print("🤖 正在唤醒亚马逊政策问答机器人...\n")

    # 1. 实例大模型
    llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),  #
            api_key=os.getenv("OPENAI_API_KEY"),  #
            model="deepseek-chat",
            temperature=0.7
        )

    # 2. 向量检索器，与生成向量模型相同
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 加载本地向量数据库
    try:
        vectorstore = FAISS.load_local(
            "knowledge_base/faiss_index",
            embeddings,
            allow_dangerous_deserialization=True  # 允许加载本地文件
        )
    except Exception as e:
        print("❌ 找不到本地向量数据库，请先运行 build_knowledge.py")
        return

    # 将数据库转化为检索器，设置每次召回最相关的 2 个片段 (k=2)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # 3. 构造RAG专用提示词模板
    system_prompt = (
        "你是亚马逊金牌店铺的内部政策问答助手。"
        "请严格根据以下提供的【参考资料】来回答用户的问题。"
        "如果【参考资料】中没有相关内容，请直接回答'抱歉，政策手册中未找到相关规定'，绝对不要自己编造答案！\n\n"
        "【参考资料】：\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. 组装RAG链路（chain）
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 5. 开始问答测试
    print("=" * 50)
    print("📚 内部政策问答系统已上线 (输入 'q' 退出)")
    print("=" * 50)

    while True:
        user_input = input("\n👤 提问: ")
        if user_input.lower() in ['q', 'quit']:
            break

        # 调用 RAG 链
        response = rag_chain.invoke({"input": user_input})

        # 打印大模型的回答
        print(f"🤖 回答: {response['answer']}")

        # 💡 工程探针：打印出到底检索到了哪些原文片段（方便调试）
        print("\n🔍 [调试信息] 本次回答参考了以下知识切片：")
        for i, doc in enumerate(response['context']):
            # 把换行符去掉，方便在一行里查看
            clean_text = doc.page_content.replace('\n', ' ')
            print(f"  片段 {i + 1}: ...{clean_text}...")


if __name__ == "__main__":
    main()

