import pandas as pd


# 未注明类型，也不知道返回什么
def greet(name):
    return "hello" + name

#新写法（工程规范）：指出name类型和返回类型
def greet_engineer(name:str)->str:
    return f"hello,{name}!Ready to code?"

# 复杂类型提示
def process_prices(prices: list[float]) -> float:
    return sum(prices) / len(prices)

def calculate_discount(price: float, discount_rate: float) -> float:
    """
    计算打折后的商品价格。

    Args:
        price(float):商品原价
        discount_rate(float):折扣率

     Returns:
        float: 打折后的最终价格
    """
    return price * (1 - discount_rate)

def safe_divide(a: float, b: float) -> float:
    try:
        # 尝试执行可能出现错误的代码
        result = a / b
        return result
    except ZeroDivisionError:
        # 如果发生ZeroDivisionError，执行这里
        print("❌ 错误：除数不能为0")
        return 0.0
    except ValueError as e:
        # 捕获其他所有意外错误
        print(f"❌ 发生未知错误：{e}")
        return 0.0
    finally:
        # 无论错误与否都会执行
        print("🔄 计算尝试结束。")

print(safe_divide(10, 2))   # 正常
print(safe_divide(10, 0))   # 触发异常
