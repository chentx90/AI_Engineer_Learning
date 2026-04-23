import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


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

