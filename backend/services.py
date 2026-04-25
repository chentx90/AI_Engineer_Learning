import os
import logging

import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, ChatMessage, ToolMessage, SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.tools import tool

load_dotenv()

class ECommerceCopywriterService:
    """文案生成模型"""
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
    """问题重写模型"""
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


@tool
def query_order_status(order_id: str) -> str:
    """定义工具tool，当用户查询订单信息时，必须调用此工具，需要传入订单号"""
    print(f" ->[后台系统],正在查询数据库，订单号：{order_id}")
    if "123" in order_id:
        return f"订单{order_id}：已发货，顺丰快递，预计，明天上午送达"
    elif "999" in order_id:
        return f"订单{order_id}：处理中，待发货"
    else:
        return f"未找到订单{order_id}的信息"

@tool
async def convert_currency(from_currency: str, to_currency: str, amount: float) -> str:
    """
        查询实时汇率并进行货币转换。适用于跨境订单价格计算。
        参数：
            from_currency (str): 源货币代码，例如 USD, EUR, CNY
            to_currency (str): 目标货币代码
            amount (float): 需要转换的金额
        """
    url = os.getenv("EXCHANGERATE_API_BASE") + from_currency.upper()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            rates = data.get("conversion_rates", {})
            rate = rates.get(to_currency.upper())
            result = amount * rate
            return f"💰 {amount:.2f} {from_currency.upper()} = {result:.2f} {to_currency.upper()}（汇率: 1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}）"
    except httpx.HTTPStatusError as e:
        return f"❌ 汇率查询失败：HTTP {e.response.status_code}，请检查 API Key 或货币代码是否正确。"
    except Exception as e:
        return f"❌ 汇率服务异常：{str(e)}"

available_tools = [query_order_status, convert_currency]
tool_map = {tool.name: tool for tool in available_tools}

class ECommerceAgentService:
    """工具调用模型"""
    def __init__(self):
        self.logger = logging.getLogger("ECommerceService")
        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL"),
            temperature=0.1
        )
        self.llm_with_tools = self.llm.bind_tools(available_tools)
    # 将工具绑定到大模型上,让大模型知道它有哪些工具可用，并在需要时输出 tool_calls 结构
    async def agent_chat_async(self, question: str, chat_history: list) -> dict:
        self.logger.info(f"收到agent请求{question}")
        messages = [
            SystemMessage(content="你是亚马逊高级客服。优先使用工具查询订单,获取汇率信息，不要瞎编。"),
            ] + chat_history + [HumanMessage(content=question)]

        intermediate_steps = []

        #  Agent 行动思考循环 (最多三轮)
        for _ in range(3):
            ai_response = await self.llm_with_tools.ainvoke(messages)
            messages.append(ai_response)   # 把AI思考加入历史
            #检查工具是否要求调用工具
            if ai_response.tool_calls:
                for tool_call in ai_response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    self.logger.info(f"AI 决定调用工具{tool_name}, 参数{tool_args}")
                    selected_tool = tool_map[tool_name]   # 找工具
                    tool_output = await selected_tool.ainvoke(tool_args)   # 用工具
                    messages.append(ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_call["id"]   # 必须带上 ID，大模型才能对上
                    ))
            else:
            # 如果没有 tool_calls，说明大模型已经得出了最终答案，跳出循环
                break

        final_answer = ai_response.content if ai_response.content else "抱歉，我无法处理该请求。"

        return {
            "answer": final_answer,
            "intermediate_steps": intermediate_steps # 把工具调用记录也返回去
        }




