import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, ChatMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough, RunnableBranch

load_dotenv()

class ECommerceCopywriterService:
    def __init__(self):
        self.logger = logging.getLogger("CopywriterService")
        self.logger.info("初始化大模型服务...")

        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL"),
            temperature=0.7
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个经验丰富的亚马逊电商金牌运营。请为商品写一段吸引人的产品描述，语气需保持【{tone}】。"),
            ("human", "商品名称：{product_name}\n核心卖点：{features}\n请生成营销文案：")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    async def generate_copy_async(self, product_name: str, features: str, tone: str) -> str:
        self.logger.info(f"正在异步生成文案: {product_name} (语气: {tone})")

        result = await self.chain.ainvoke({
            "product_name": product_name,
            "features": features,
            "tone": tone
        })

        return result

def convert_history_to_langchain(chat_history: list[ChatMessage]) -> list:
    """
    将 Pydantic 的 ChatMessage 列表，转换为 LangChain 的 BaseMessage 列表。
    这是连接 Web 前端与 LangChain 核心引擎的关键桥梁！
    """
    langchain_history = []
    for msg in chat_history:
        if msg.role=="human":
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role=="ai":
            langchain_history.append(AIMessage(content=msg.content))
    return langchain_history

# 辅助函数拼接文档
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class RAGPolicyService:
    def __init__(self):
        self.logger = logging.getLogger("RAGPolicyService")
        self.logger.info("初始化访问策略问答服务...")

        # 1. 组件准备
        llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL"),
            temperature=0.7
        )
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local(
            "data-cleaner/ai_tools/knowledge_base/faiss_index",
            embeddings,
            allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

        # 问题重写
        contextualize_q_system_prompt = (
            "给定聊天历史记录和用户最新提出的问题，"
            "该问题可能会引用聊天历史记录中的上下文。"
            "请制定一个独立的问题，使其在没有聊天历史记录的情况下也能被理解。"
            "你只需要重写问题，不要回答它。"
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])
        query_rewrite_chain = RunnableBranch(
            (lambda x: bool(x.get("chat_history")), contextualize_q_prompt| llm | StrOutputParser()),
            (lambda x: x["question"])
        )

        # 3. 最终 QA 链 (与昨天一致)
        qa_system_prompt = (
            "你是亚马逊金牌店铺的内部政策问答助手。"
            "请严格根据以下提供的【参考资料】来回答用户的问题。"
            "如果资料中没有相关内容，请直接回答'抱歉，政策手册中未找到相关规定'，绝不编造。\n\n"
            "【参考资料】：\n{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        # 4. 组装终极 LCEL 链
        self.chain = (
            RunnablePassthrough.assign(context=query_rewrite_chain | retriever | format_docs)
            | qa_prompt
            | llm
            | StrOutputParser()
        )
        self.logger.info("RAG 服务初始化完成！")

    # 5. 异步调用入口
    async def ask_policy_async(self, question: str, chat_history_lc: list) -> str:
        self.logger.info(f"收到 RAG 请求: {question}")

        result = await self.chain.ainvoke({
            "question": question,
            "chat_history": chat_history_lc
        })
        return result





