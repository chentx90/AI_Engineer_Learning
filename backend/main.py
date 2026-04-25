from fastapi import FastAPI
from pydantic import BaseModel, Field
from services import convert_history_to_langchain, ECommerceCopywriterService, RAGPolicyService, ECommerceAgentService
from typing import List, Literal


# 实列化FastAPI应用
app = FastAPI(title="亚马逊智能助手API", version="0.1.0")

# 在应用启动时，实例化服务（作为全局单例，避免每次请求都重新初始化大模型）
copywriter_service = ECommerceCopywriterService()
rag_service = RAGPolicyService()
agent_service = ECommerceAgentService()

# 定义聊天记录模型
class ChatMessage(BaseModel):
    role: Literal["human", "ai"] = Field(..., description="消息源", json_schema_extra={"example": "human"})
    content: str = Field(..., description="消息内容", json_schema_extra={"example":"电子产品退货期多久？"})

# 定义RAG请求模型
class RAGChatMessage(BaseModel):
    question: str = Field(..., description="用户最新提问", json_schema_extra={"example":"那运费谁出？"})
    chat_history: List[ChatMessage] = Field(default=list, description="历史聊天记录为空")

# 定义RAG响应模型
class RAGChatResponse(BaseModel):
    answer: str
    status: str = "success"


class CopywriterRequest(BaseModel):
    product_name: str = Field(..., description="商品名称", json_schema_extra={"example": "人体工学鼠标"})
    features: str = Field(..., description="核心卖点，", json_schema_extra={"example": "静音，Type-C快充"})
    tone: str = Field(default="专业", description="文案语气（专业/幽默/热情")

#定义响应体结构
class CopywriterResponse(BaseModel):
    product_name: str
    generated_copy: str
    status: str = "success"

# 3. 定义 Pydantic 模型
class AgentChatRequest(BaseModel):
    question: str = Field(..., description="用户问题", json_schema_extra={"example": "查一下订单 123 发货了吗？"})
    chat_history: List[ChatMessage] = Field(default_factory=list)

class AgentChatResponse(BaseModel):
    answer: str
    intermediate_steps: list = Field(description="AI调用的工具详情", default_factory=list)
    status: str = "success"


# 定义Routing和GET请求
@app.get("/")
def read_root():
    return {"Message": "欢迎来到智能助手后端！", "status": "running"}

@app.get("/hello/{name}")
def say_hello(name: str):
    return {"Message": f"Hello, {name}!"}

# 定义POST接口
@app.post("/api/generate_copy", response_model=CopywriterResponse)
async def generate_copy_api(request: CopywriterRequest):
    real_copy = await copywriter_service.generate_copy_async(
        request.product_name,
        request.features,
        request.tone
    )

# 返回符合 CopywriterResponse 结构的数据
    return CopywriterResponse(
        product_name=request.product_name,
        generated_copy=real_copy
    )

@app.post("/api/rag/ask", response_model=RAGChatResponse)
async def ask_policy_api(request:RAGChatMessage):
    """
    亚马逊内部政策问答接口（支持多轮对话）
    """
    # 转换消息列表
    lc_chat_history = convert_history_to_langchain(request.chat_history)
    # 异步调用方法
    answer = await rag_service.ask_policy_async(
        question=request.question,
        chat_history_lc=lc_chat_history
    )
    return RAGChatResponse(
        answer=answer
    )


@app.post("/api/agent/chat", response_model=AgentChatResponse)
async def agent_chat_api(request: AgentChatRequest):
    # 转换历史记录 (复用上午的函数)
    lc_chat_history = convert_history_to_langchain(request.chat_history)

    # 调用 Agent 服务
    result = await agent_service.agent_chat_async(
        question=request.question,
        chat_history=lc_chat_history
    )

    return AgentChatResponse(
        answer=result["answer"],
        intermediate_steps=result["intermediate_steps"]
    )



