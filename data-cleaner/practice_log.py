import logging


# 1. 配置日志系统
logging.basicConfig(
    level=logging.INFO,   # 设置最低显示级别：DEBUG < INFO < WARNING < ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 2. 获取一个日志提取器
logger = logging.getLogger('MyAgent')

# 3. 使用不同级别日志替代
logger.debug("这是一条详细的调试信息")
logger.info("程序正常启动。")
logger.warning("警告：这是一条警告！")
logger.error("错误：这是一条错误信息！！！")
