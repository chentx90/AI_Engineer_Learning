import os
import logging
from dotenv import load_dotenv
from langchain_classic.chains import history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS


load_dotenv()
logging.basicConfig(level=logging.WARNING)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def main():
    print("🤖 正在唤醒亚马逊政策问答机器人...\n")

    # 1. 实例大模型
    llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),  #
            api_key=os.getenv("OPENAI_API_KEY"),  #
            model="deepseek-chat",
            temperature=0.1
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

    # 2. 构建“问题重写器” (History-Aware Retriever)
    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system","给定聊天历史记录和用户最新提出的问题，"
                 "该问题可能会引用聊天历史记录中的上下文（比如使用了代词'它'）。"
                 "请制定一个独立的问题，使其在没有聊天历史记录的情况下也能被理解。"
                 "你只需要重写问题，不要回答它。如果不需要重写，就原样返回。"),
        (MessagesPlaceholder(variable_name="chat_history")),
        ("human", "{question}"),
    ])

    # RunnableBranch 充当路由器：
    # 条件：如果输入字典中的 "chat_history" 有内容
    # -> 执行：重写 Prompt | 大模型 | 字符串解析器
    # 否则 -> 直接返回原问题
    query_rewrite_chain = RunnableBranch(
        (lambda x: bool(x.get("chat_history")), rewrite_prompt | llm | StrOutputParser()),
        (lambda x: x["question"])
    )

    # 3. 构造RAG专用提示词模板
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是亚马逊金牌店铺的内部政策问答助手。"
                   "请严格根据以下提供的【参考资料】来回答用户的问题。"
                   "如果资料中没有相关内容，请回答'抱歉，政策手册中未找到相关规定'，绝不编造。\n\n"
                   "【参考资料】：\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    # 4. 组装RAG链路
    rag_chain = (
        RunnablePassthrough.assign(# 数据流：输入字典 -> 问题重写链 -> 检索器 -> 格式化文档文本 -> 存入 'context'
        context=query_rewrite_chain | retriever | format_docs)
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    # 5. 开始聊天循环
    chat_history = []

    print("=" * 50)
    print("📚 内部政策问答系统已上线 (输入 'q' 退出)")
    print("=" * 50)

    while True:
        user_input = input("\n👤 提问: ")
        if user_input.lower() in ['q', 'quit']:
            break

        # 触发 LCEL 链，传入初始字典
        answer = rag_chain.invoke({
            "question": user_input,
            "chat_history": chat_history
        })

        print(f"🤖 回答: {answer}")

        # 将本次对话加入历史
        chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=answer)
        ])

        # 滑动窗口 (保留最近 3 轮对话)
        if len(chat_history) > 6:
            chat_history = chat_history[-6:]

if __name__ == "__main__":
    main()

