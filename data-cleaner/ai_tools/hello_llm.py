import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 1. 加载.env中的环境变量
load_dotenv()

def main():
    print("正在唤醒大模型...")

    # 2. 实例化大模型
    llm = ChatOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),  #
        api_key=os.getenv("OPENAI_API_KEY"),  #
        model="deepseek-chat",
        temperature=0.7
    )

    # 3. 向模型提问
    response = llm.invoke("你好，请用一句话介绍什么是AI Agent")

    print(response.content)

if __name__ == "__main__":
    main()


