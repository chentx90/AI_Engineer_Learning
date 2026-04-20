import argparse
import pandas as pd
import sys
import logging

class AmazonDataCleaner:
    def __init__(self, input_path:str, output_path:str ):
        self.input_path = input_path
        self.output_path = output_path
        self.df = None  # 储蓄数据状态

        # 配置专属日志器
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("DataCleaner")

    def load_data(self):
        """安全加载CSV文件,

        Args:
            file_path （str): CSV文件的绝对或相对路径

        Returns：
            pd.DataFrame: 加载数据，若失败则退出程序
        """
        try:
            self.df = pd.read_csv(self.input_path)
        except FileNotFoundError:
            self.logger.error(f"❌ 严重错误：找不到文件 '{self.input_path}'。请检查路径是否正确！")
            sys.exit(1)    # 找不到源文件，强行退出程序
        except pd.errors.EmptyDataError:
            self.logger.error(f"❌ 严重错误：文件 '{self.input_path}'是空的！")
            sys.exit(1)

    def clean_price_column(self):
        """清洗价格列，处理缺失值，移除货币符号，转换为浮点数"""
        # 注意：现在数据存在 self.df 里，不需要传来传去了！
        if 'price' not in self.df.columns:
            self.logger.warning("⚠️ 数据中不存在'price'列，跳过清洗")
            return None
        original_missing = self.df['price'].isnull().sum()

        # 移除美元货币符号
        self.df['price'] = self.df['price'].astype(str).str.replace('$', '', regex=False)

        # 将空字符串和'nan',转换成真正的NaN
        self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')

        # 用列中位数填充缺失值
        median_value = self.df['price'].median()
        self.df['price'].fillna(median_value, inplace=True)

        self.logger.info("价格清洗完成")
        return None

    def parse_dates(self):
        """确保日期列格式为正确的datetime格式"""
        self.df['last_updated'] = pd.to_datetime(self.df['last_updated'], errors='coerce')
        self.logger.info("日期列为正确的datetime格式")
        return None

    def run(self):
        """执行完整工作流"""
        self.logger.info("🛒 开始电商数据清洗任务...")
        self.load_data()
        self.clean_price_column()
        self.parse_dates()
        self.df.to_csv(self.output_path, index=False)
        self.logger.info("✨ 任务圆满结束！")

def main():
    """主函数：执行完整清理流程"""
    # 1. 设置argparse
    parser = argparse.ArgumentParser(description="数据清洗器CLI工具 v0.2")

    # 设置input, output参数
    parser.add_argument(
        "-i", "--input",
        type = str,
        required = True,
        help = "输入的原始 CSV 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        type = str,
        default = "cleaned_result.csv",
        help="输出的 CSV 文件路径"
    )

    args = parser.parse_args()

    cleaner = AmazonDataCleaner(args.input, args.output)
    cleaner.run()
    
if __name__ == "__main__":
    main()