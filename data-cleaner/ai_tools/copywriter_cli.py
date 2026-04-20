import argparse
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os


#  加载环境变量
load_dotenv()

class ECommerceCopywriter:
    def __init__(self, model_name: str = "deepseek-chat"):
        # 配置日志
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化大模型...")

        self.llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),  #
            api_key=os.getenv("OPENAI_API_KEY"),  #
            model="deepseek-chat",
            temperature=0.7
        )

        # 定义提诗词模板
        # {product_name} 和 {features} 是我们要动态填入的变量
        self.prompt_template = PromptTemplate(
            input_variables=["product_name", "features"],
            template="""
            你是一个经验丰富的亚马逊电商金牌运营。
            请为以下商品写一段吸引人的产品描述（约100字），突出卖点，激发购买欲。
            
            商品名称：{product_name}
            核心卖点：{features}
            
            营销文案:
            """
        )

    def generate_copy(self, product_name: str, features: str) -> str:
        self.logger.info(f"正在为 [{product_name}] 生成文案...")

        # 1. 将变量填入模板，生成最终的 Prompt 字符串
        final_prompt = self.prompt_template.format(product_name=product_name, features=features)

        # 2. 调用模型
        response = self.llm.invoke(final_prompt)

        return response.content

def main():
    parser = argparse.ArgumentParser(description="电商AI文案生成器")
    parser.add_argument("-p", "--product", type=str, required=True, help="商品名称")
    parser.add_argument("-f", "--features", type=str, required=True, help="核心卖点，用逗号分隔")

    args = parser.parse_args()

    # 实例化并运行
    writer = ECommerceCopywriter(model_name="deepseek-chat")  # 如果你用其他模型，这里传入 model_name="你的模型"
    result = writer.generate_copy(args.product, args.features)

    print("\n" + "="*50)
    print("✍️ 生成的电商文案：")
    print("="*50)
    print(result)
    print("="*50)

if __name__ == "__main__":
    main()



