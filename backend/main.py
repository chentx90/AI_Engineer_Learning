from fastapi import FastAPI
from pydantic import BaseModel, Field
from services import ECommerceCopywriterService


# 实列化FastAPI应用
app = FastAPI(title="亚马逊智能助手API", version="0.1.0")

# 在应用启动时，实例化服务（作为全局单例，避免每次请求都重新初始化大模型）
copywriter_service = ECommerceCopywriterService()

class CopywriterRequest(BaseModel):
    product_name: str = Field(..., description="商品名称", json_schema_extra={"example": "人体工学鼠标"})
    features: str = Field(..., description="核心卖点，", json_schema_extra={"example": "静音，Type-C快充"})
    tone: str = Field(default="专业", description="文案语气（专业/幽默/热情")

#定义响应体结构
class CopywriterResponse(BaseModel):
    product_name: str
    generated_copy: str
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



