# 1. 定义一个模板类
class DummyAgent:
    # 2. 初始化方法（这个类创建时的初始状态）
    def __init__(self, name: str, role: str):
        self.name = name   # 定义属性
        self.role = role
        self.memory = []   # agent记忆初始为空

    # 3. 定义行为方法
    def observe(self, message: str):
        print(f"[{self.name} 观察到]: {message}")
        self.memory.append(message)

    def think(self) -> str:
        if not self.memory:
            return "我的脑子空空..."
        return f"我正在思考这 {len(self.memory)} 条信息..."

# 4. 实例化
agent_a = DummyAgent(name="小娜", role="客服助理")
agent_b = DummyAgent(name="小克", role="数据分析师")

# 5. 调用实例
agent_a.observe("客户问退货政策")
agent_b.observe("客户情绪有些激动")
print(agent_a.think())

print(f"{agent_b.name} 的记忆：{agent_b.memory}")   # 小克记忆独立
